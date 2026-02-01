from bluer_algo.tracker.factory import LIST_OF_TRACKER_ALGO

docs = [
    {
        "path": "../docs/tracker",
    }
] + [
    {
        "path": f"../docs/tracker/{algo}.md",
    }
    for algo in LIST_OF_TRACKER_ALGO
]
