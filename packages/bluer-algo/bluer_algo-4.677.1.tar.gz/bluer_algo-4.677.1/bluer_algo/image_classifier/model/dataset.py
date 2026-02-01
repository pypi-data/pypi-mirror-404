import os
from torch.utils.data import Dataset
from PIL import Image


class ImageDataset(Dataset):
    def __init__(self, df, root_dir, transform=None):
        self.df = df.reset_index(drop=True)
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        img_name = os.path.join(self.root_dir, self.df.loc[idx, "filename"])
        image = Image.open(img_name).convert("RGB")
        label = int(self.df.loc[idx, "class_index"])
        if self.transform:
            image = self.transform(image)
        return image, label
