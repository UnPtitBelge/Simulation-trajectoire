import os

def findLastDirNumber(path: str, dirName: str) -> int:
    lastNumber = -1
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)) and item.startswith(dirName):
            try:
                number = int(item[len(dirName):])
                if number > lastNumber:
                    lastNumber = number
            except ValueError:
                continue
    return lastNumber

def findLastFileNumber(path: str, filePrefix: str, fileSuffix: str) -> int:
    lastNumber = -1
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)) and item.startswith(filePrefix) and item.endswith(fileSuffix):
            try:
                number = int(item[len(filePrefix):-len(fileSuffix)])
                if number > lastNumber:
                    lastNumber = number
            except ValueError:
                continue
    return lastNumber

def set_video_filename(path: str, filePrefix: str, fileSuffix: str) -> str:
    lastNumber = findLastFileNumber(path, filePrefix + '_', fileSuffix)
    newNumber = lastNumber + 1
    return f"{filePrefix}_{newNumber}{fileSuffix}"

def create_necessary_dirs(path: str, dirName: str) -> None:
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, dirName), exist_ok=True)
