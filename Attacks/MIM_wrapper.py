import time

import Attacks.MIM_attack as Mim
from tensorflow.contrib.keras.api.keras.models import load_model
import tensorflow as tf
import numpy as np

from datasets.setup_mnist import MNIST


def loss(correct, predicted):
    return tf.nn.softmax_cross_entropy_with_logits(labels=correct,
                                                   logits=predicted)

def MIM(model, sess, epsilon, num_steps, data=MNIST()):


    image_size = data.test_data.shape[1]
    num_channels = data.test_data.shape[3]
    num_labels = data.test_labels.shape[1]

    shape = (None, image_size, image_size, num_channels)
    model.x_input = tf.placeholder(tf.float32, shape)
    model.y_input = tf.placeholder(tf.float32, [None, num_labels])

    pre_softmax = model(model.x_input)
    y_loss = tf.nn.softmax_cross_entropy_with_logits(labels=model.y_input, logits=pre_softmax)
    model.xent = tf.reduce_sum(y_loss)

    attack = Mim.MimAttack(model, epsilon, num_steps)
    if data.dataset == "cifar":
        sets = np.split(data.test_data, 2)
        label_sets = np.split(data.test_labels, 2)

        p1 = attack.perturb(sets[0], label_sets[0], sess)
        p2 = attack.perturb(sets[1], label_sets[1], sess)
        return np.concatenate((p1, p2), axis=0)

    return attack.perturb(np.array(data.test_data), np.array(data.test_labels), sess)

def get_accuracy(file_name, sess, epsilon, num_steps, step_size, data=MNIST()):
    model = load_model(file_name, custom_objects={'fn': loss, 'tf': tf, 'atan': tf.math.atan})
    start_time = time.time()
    adversaries = MIM(model, sess, epsilon, num_steps, data)
    predictions = model.predict(adversaries)
    accuracy = np.mean(np.equal(np.argmax(predictions, 1), np.argmax(data.test_labels, 1)))
    print(f"The accuracy was {accuracy}", flush=True)
    time_used = time.time() - start_time

    return accuracy, time_used
