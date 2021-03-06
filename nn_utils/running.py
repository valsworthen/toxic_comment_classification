import numpy as np
from keras.callbacks import Callback
from keras.callbacks import EarlyStopping, ModelCheckpoint
import keras.backend as K
from sklearn.metrics import roc_auc_score

class RocAucEvaluation(Callback):
    """This callback computes AUC on the validation data which allows us to monitor training"""
    def __init__(self, filepath = None, validation_data=()):
        super(Callback, self).__init__()
        self.filepath = filepath
        self.best = 0
        self.X_val, self.y_val = validation_data
        self.y_pred = np.zeros(self.y_val.shape)

    def on_epoch_end(self, epoch, logs={}):
        y_pred = self.model.predict(self.X_val, verbose=0)
        current = roc_auc_score(self.y_val, y_pred)
        logs['roc_auc_val'] = current

        if current > self.best: #save model
            self.best = current
            self.y_pred = y_pred
            if self.filepath:
                self.model.save(self.filepath, overwrite = True)
        print("--- AUC - epoch: {:d} - score: {:.5f}".format(epoch+1, current))

class DisplayLR(Callback):
    def on_epoch_end(self, epoch, logs=None):
        lr = self.model.optimizer.lr
        decay = self.model.optimizer.decay
        iterations = self.model.optimizer.iterations
        lr_with_decay = lr / (1. + decay * K.cast(iterations, K.dtype(decay)))
        print('\nLearning rate for next epoch: ',K.eval(lr_with_decay))


def fitting_model(model, X_train, Y_train, X_valid, Y_valid, training_params, filepath):
    lrdisplay = DisplayLR()
    ra_val = RocAucEvaluation(validation_data=(X_valid, Y_valid))
    checkpoint = ModelCheckpoint(filepath, monitor=training_params['monitored_value'], verbose=1, save_best_only=True, save_weights_only = True)
    es = EarlyStopping(monitor=training_params['monitored_value'], min_delta = training_params['min_delta'],
                                patience=training_params['patience'], mode='auto', verbose=1)

    hist = model.fit(X_train, Y_train, epochs = training_params['nb_epochs'], batch_size= training_params['batch_size'],
                    callbacks = [ra_val, checkpoint, es], validation_data = (X_valid, Y_valid))
    return hist.history, es.stopped_epoch
