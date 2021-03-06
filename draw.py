import os
import numpy as np
import tensorflow as tf
from datasets import data as dataset
from models.retina import RetinaNet as ConvNet
from learning.evaluators import RecallEvaluator as Evaluator
from learning.utils import get_boxes, cal_recall
from utils.visualization import draw_pred_boxes
import cv2
import glob
import time

""" 1. Load dataset """
root_dir = os.path.join('data/face')
test_dir = os.path.join(root_dir, 'draw')
IM_SIZE = (544, 960)
NUM_CLASSES = 1

# Load test set
X_test, y_test = dataset.read_data(test_dir, IM_SIZE, no_label=True)
test_set = dataset.DataSet(X_test, y_test)

""" 2. Set test hyperparameters """
class_map = dataset.load_json(os.path.join(test_dir, 'classes.json'))
nms_flag = True
hp_d = dict()
hp_d['batch_size'] = 1
hp_d['nms_flag'] = nms_flag
hp_d['frontend'] = 'resnet_v2_50'

""" 3. Build graph, load weights, initialize a session and start test """
# Initialize
graph = tf.get_default_graph()
config = tf.ConfigProto()
config.gpu_options.allow_growth = True

model = ConvNet([IM_SIZE[0], IM_SIZE[1], 3], NUM_CLASSES, **hp_d)
evaluator = Evaluator()
saver = tf.train.Saver()

sess = tf.Session(graph=graph, config=config)
saver.restore(sess, './model.ckpt')
start_time = time.time()
test_y_pred = model.predict(sess, test_set, **hp_d)
end_time = time.time()

print('Takt time: {}'.format((end_time - start_time) * 1000 / len(y_test)))

""" 4. Draw boxes on image """
draw_dir = os.path.join(test_dir, 'draws') # FIXME
im_dir = os.path.join(test_dir, 'images') # FIXME
im_paths = []
im_paths.extend(glob.glob(os.path.join(im_dir, '*.jpg')))
for idx, (img, y_pred, im_path) in enumerate(zip(test_set.images, test_y_pred, im_paths)):
# for idx, (img, y_pred, im_path) in enumerate(zip(test_set.images, test_set.labels, im_paths)):
    name = im_path.split('/')[-1]
    draw_path =os.path.join(draw_dir, name)
    bboxes = get_boxes(y_pred, model.anchors)
    bboxes = bboxes[np.nonzero(np.any(bboxes > 0, axis=1))]
    boxed_img = draw_pred_boxes(img, bboxes, class_map)
    cv2.imwrite(draw_path, boxed_img)
