import torch
from torch import nn
from torch import optim
from torchvision import transforms
from torch.utils.data import DataLoader
from tqdm import tqdm, trange
from typing import List
import matplotlib.pyplot as plt
import numpy as np

from blueness import module
from bluer_objects import objects
from bluer_objects.metadata import post_to_object
from bluer_objects import file
from bluer_objects.graphics.signature import justify_text
from bluer_objects.logger.image import (
    log_image_grid,
    LOG_IMAGE_GRID_COLS,
    LOG_IMAGE_GRID_ROWS,
)

from bluer_algo import NAME
from bluer_algo.host import signature
from bluer_algo.image_classifier.dataset.dataset import ImageClassifierDataset
from bluer_algo.image_classifier.model.dataset import ImageDataset
from bluer_algo.image_classifier.model.model import TinyCNN
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def train(
    dataset_object_name: str,
    model_object_name: str,
    batch_size: int = 16,
    num_epochs: int = 10,
    log: bool = True,
    verbose: bool = False,
    line_width: int = 80,
) -> bool:
    logger.info(
        "{}.train: {} -> {}".format(
            NAME,
            dataset_object_name,
            model_object_name,
        )
    )

    success, dataset = ImageClassifierDataset.load(
        object_name=dataset_object_name,
    )
    if not success:
        return success

    object_path = objects.object_path(
        object_name=dataset.object_name,
    )
    num_workers = 2 if torch.cuda.is_available() else 0
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logger.info(
        "transforms: {} x {}".format(
            dataset.shape[0],
            dataset.shape[1],
        )
    )
    transform = transforms.Compose(
        [
            transforms.Resize((dataset.shape[0], dataset.shape[1])),
            transforms.ToTensor(),
        ]
    )

    train_df = dataset.df[dataset.df["subset"] == "train"]
    eval_df = dataset.df[dataset.df["subset"] == "eval"]

    train_set = ImageDataset(train_df, object_path, transform)
    eval_set = ImageDataset(eval_df, object_path, transform)

    train_loader = DataLoader(
        train_set,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
    )
    eval_loader = DataLoader(
        eval_set,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
    )

    model = TinyCNN(num_classes=dataset.class_count).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    logger.info("training...")
    epoch_loss_list: List[float] = []
    for epoch in trange(num_epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)

        epoch_loss = float(running_loss / len(train_loader.dataset))
        epoch_loss_list.append(epoch_loss)
        logger.info(f"epoch #{epoch+1}, loss: {epoch_loss:.4f}")

    logger.info("evaluating...")
    model.eval()
    correct = total = 0
    log_items = []
    confusion_matrix = np.zeros((dataset.class_count, dataset.class_count))
    with torch.no_grad():
        for images, labels in tqdm(eval_loader):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            for image, label, prediction in zip(images, labels, predicted):
                confusion_matrix[int(label), int(prediction)] += 1

                if len(log_items) >= LOG_IMAGE_GRID_COLS * LOG_IMAGE_GRID_ROWS:
                    continue
                log_items.append(
                    {
                        "image": np.transpose(image, (1, 2, 0)),
                        "title": (
                            dataset.dict_of_classes[int(label)]
                            if label == prediction
                            else "{} <> {}".format(
                                dataset.dict_of_classes[int(prediction)],
                                dataset.dict_of_classes[int(label)],
                            )
                        ),
                        "color": "black" if label == prediction else "red",
                    }
                )
    eval_accuracy = correct / total

    confusion_matrix = confusion_matrix / confusion_matrix.sum(
        axis=1,
        keepdims=True,
    )
    confusion_matrix = np.nan_to_num(confusion_matrix)

    logger.info("accuracy:")
    logger.info(f" - eval: {100 * eval_accuracy:.2f}%")
    for class_index in range(dataset.class_count):
        logger.info(
            " - {}: {:.2f}%".format(
                dataset.dict_of_classes[class_index],
                100 * confusion_matrix[class_index, class_index],
            )
        )

    # prep for visualization
    header = (
        objects.signature(object_name=dataset_object_name)
        + dataset.signature()
        + [
            f"batch_size: {batch_size}",
            f"num_epochs: {num_epochs}",
            f"eval_accuracy: {100*eval_accuracy:.2f}%",
        ]
    )

    # evaluation.png
    if not log_image_grid(
        items=log_items,
        filename=objects.path_of(
            object_name=model_object_name,
            filename="evaluation.png",
        ),
        header=header,
        footer=signature(),
        log=log,
    ):
        return False

    header.append(f"model: {model_object_name}")

    # confusion_matrix.png
    fig, ax = plt.subplots(figsize=(10, 10))
    cax = ax.imshow(
        confusion_matrix,
        interpolation="nearest",
        cmap=plt.cm.Blues,
    )
    fig.colorbar(cax)
    ax.set_title(
        justify_text(
            " | ".join(header),
            line_width=line_width,
            return_str=True,
        )
    )
    ax.set_xlabel(
        justify_text(
            " | ".join(["prediction"] + signature()),
            line_width=line_width,
            return_str=True,
        )
    )
    ax.set_ylabel("Label")
    ax.set_xticks(np.arange(dataset.class_count))
    ax.set_yticks(np.arange(dataset.class_count))
    ax.set_xticklabels(
        [dataset.dict_of_classes[value] for value in np.arange(dataset.class_count)],
        rotation=45,
        ha="right",
    )
    ax.set_yticklabels(
        [dataset.dict_of_classes[value] for value in np.arange(dataset.class_count)]
    )
    thresh = confusion_matrix.max() / 2.0
    for i in range(confusion_matrix.shape[0]):
        for j in range(confusion_matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{100*confusion_matrix[i, j]:.1f}%",
                ha="center",
                va="center",
                color="white" if confusion_matrix[i, j] > thresh else "black",
            )
    plt.tight_layout()
    if not file.save_fig(
        objects.path_of(
            object_name=model_object_name,
            filename="confusion_matrix.png",
        ),
        log=log,
    ):
        return False

    # loss.png
    plt.figure(figsize=(10, 5))
    plt.plot(
        range(num_epochs),
        epoch_loss_list,
        marker="o",
    )
    plt.xlabel(
        justify_text(
            " | ".join(["Epoch"] + signature()),
            line_width=line_width,
            return_str=True,
        )
    )
    plt.ylabel("Loss")
    plt.title(
        justify_text(
            " | ".join(header),
            line_width=line_width,
            return_str=True,
        )
    )
    plt.grid(True)
    if not file.save_fig(
        objects.path_of(
            object_name=model_object_name,
            filename="loss.png",
        ),
        log=log,
    ):
        return False

    if not file.save_matrix(
        objects.path_of(
            object_name=model_object_name,
            filename="confusion_matrix.npy",
        ),
        confusion_matrix,
        log=log,
    ):
        return False

    if not post_to_object(
        object_name=model_object_name,
        key="model",
        value={
            "dataset": {
                "count": dataset.count,
                "classes": dataset.dict_of_classes,
                "class_count": dataset.class_count,
                "shape": dataset.shape,
            },
            "inputs": {
                "batch_size": batch_size,
                "num_epochs": num_epochs,
                "object_name": dataset_object_name,
            },
            "training": {
                "loss": epoch_loss_list,
            },
            "evaluation": {
                "eval_accuracy": eval_accuracy,
                "class_accuracy": {
                    class_index: float(confusion_matrix[class_index, class_index])
                    for class_index in range(dataset.class_count)
                },
            },
        },
    ):
        return False

    model_filename = objects.path_of(
        object_name=model_object_name,
        filename="model.pth",
    )
    try:
        torch.save(
            model.state_dict(),
            model_filename,
        )
    except Exception as e:
        logger.error(e)
        return False

    logger.info(f"-> {model_filename}")
    return True
