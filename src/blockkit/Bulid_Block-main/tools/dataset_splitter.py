import os, shutil, random
from tqdm import tqdm

"""
标注文件是yolo格式（txt文件）
训练集：验证集：测试集 （7：2：1） 
"""


def split_img(img_path, label_path, split_list):
    try:
			#  这个是你划分结果输出的路径
        Data = './data/data_obb_1205'
        # Data是你要将要创建的文件夹路径（路径一定是相对于你当前的这个脚本而言的）
        # os.mkdir(Data)

        train_img_dir = Data + '/images/train'
        val_img_dir = Data + '/images/val'
        test_img_dir = Data + '/images/test'

        train_label_dir = Data + '/labels/train'
        val_label_dir = Data + '/labels/val'
        test_label_dir = Data + '/labels/test'

        # 创建文件夹
        os.makedirs(train_img_dir)
        os.makedirs(train_label_dir)
        os.makedirs(val_img_dir)
        os.makedirs(val_label_dir)
        os.makedirs(test_img_dir)
        os.makedirs(test_label_dir)

    except:
        print('文件目录已存在')

    train, val, test = split_list
    all_img = os.listdir(img_path)
    all_img_path = [os.path.join(img_path, img) for img in all_img]
    # all_label = os.listdir(label_path)
    # all_label_path = [os.path.join(label_path, label) for label in all_label]
    train_img = random.sample(all_img_path, int(train * len(all_img_path)))
    train_img_copy = [os.path.join(train_img_dir, img.split('\\')[-1]) for img in train_img]
    train_label = [toLabelPath(img, label_path) for img in train_img]
    train_label_copy = [os.path.join(train_label_dir, label.split('\\')[-1]) for label in train_label]
    for i in tqdm(range(len(train_img)), desc='train ', ncols=80, unit='img'):
        _copy(train_img[i], train_img_dir)
        _copy(train_label[i], train_label_dir)
        all_img_path.remove(train_img[i])
    val_img = random.sample(all_img_path, int(val / (val + test) * len(all_img_path)))
    val_label = [toLabelPath(img, label_path) for img in val_img]
    for i in tqdm(range(len(val_img)), desc='val ', ncols=80, unit='img'):
        _copy(val_img[i], val_img_dir)
        _copy(val_label[i], val_label_dir)
        all_img_path.remove(val_img[i])
    test_img = all_img_path
    test_label = [toLabelPath(img, label_path) for img in test_img]
    for i in tqdm(range(len(test_img)), desc='test ', ncols=80, unit='img'):
        _copy(test_img[i], test_img_dir)
        _copy(test_label[i], test_label_dir)


def _copy(from_path, to_path):
    shutil.copy(from_path, to_path)


# def toLabelPath(img_path, label_path):
#     img = img_path.split('\\')[-1]
#     # 修正：使用os.path.splitext分离文件名和扩展名，适用于任何图片格式
#     img_name = os.path.splitext(img)[0]  # 获取不带扩展名的文件名
#     label = img_name + '.txt'  # 生成对应的标注文件名
#     return os.path.join(label_path, label)
def toLabelPath(img_path, label_path):
    # 使用 os.path.basename 获取文件名，跨平台兼容
    img = os.path.basename(img_path)  # 这将得到如 '118.png'
    # 使用os.path.splitext分离文件名和扩展名
    img_name = os.path.splitext(img)[0]  # 获取不带扩展名的文件名
    label = img_name + '.txt'  # 生成对应的标注文件名
    return os.path.join(label_path, label)



if __name__ == '__main__':
   #  更改成你自己的需要划分图像和标签的路径
    img_path = '/home/hunter/下载/jsj/data_new/building_blocks/images/Train'  # 你的图片存放的路径（路径一定是相对于你当前的这个脚本文件而言的）
    label_path = '/home/hunter/下载/jsj/data_new/building_blocks/labels/Train'  # 你的txt文件存放的路径（路径一定是相对于你当前的这个脚本文件而言的）
    split_list = [0.7, 0.2, 0.1]  # 数据集划分比例[train:val:test]
    split_img(img_path, label_path, split_list)

