# pip install --upgrade tensorflow==1.5 for old CPU

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

from importlib import reload

import numpy as np

import math
from sklearn.metrics import mean_squared_error

import matplotlib.pyplot as plt
import datetime

import k_lstm.k_utils as k_utils

import k_lstm.my_utils as my_utils
reload(my_utils)


def get_train_data(temp_data_folder):

    train_x = my_utils.get_object(temp_data_folder+'train_x.pkl')
    train_y = my_utils.get_object(temp_data_folder+'train_y.pkl')

    print('train_x.shape:', train_x.shape)
    print('train_y.shape:', train_y.shape)
    return train_x, train_y


# create and fit the LSTM network
# ---- build a model --------
def build_model(train_x, train_y, num_neurons=20, num_epochs=20):

    # ---- model configuration ----
    # A batch size of 1 means that the model will be fit using online training (as opposed to batch training or mini-batch training).
    # As a result, it is expected that the model fit will have some variance.
    batch_size = 1
    timesteps = 1

    dropout = 0.05

    num_in = train_x.shape[1]
    print('num_in:', num_in)
    num_out = train_y.shape[1]
    print('num_out:', num_out)


    # batch_input_shape = (batch_size, timesteps, data_dim).
    # 2D array [samples, features] to a 3D array [samples, timesteps, features].
    train_x = train_x.reshape(train_x.shape[0], timesteps, num_in)
    # train_y = train_y.reshape(train_y.shape[0], timesteps, num_out)

    # -- design network ----------
    model = Sequential()
    model.add(
        LSTM(num_neurons, batch_input_shape=(batch_size, timesteps, num_in), stateful=True, return_sequences=False, dropout=dropout))
    # model.add(LSTM(30, batch_input_shape=(batch_size, timesteps, num_in), stateful=True))
    model.add(Dense(num_out, activation='linear'))
    # using the efficient ADAM optimization algorithm and the mean squared error loss function
    model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mse', 'mae', 'mape', 'cosine'])

    # fit network
    fit_history = dict(loss=[], mse=[], mae=[], mape=[], title='')  # Creating a empty list for holding the loss later
    # Ideally, more training epochs would be used (such as 1500), but this was truncated to 50 to keep run times reasonable.
    # Using all your batches once is 1 epoch.
    for i in range(num_epochs):
        print('-- Epochs -- ' + str(i))
        result = model.fit(train_x, train_y, epochs=1, batch_size=batch_size, verbose=2, shuffle=False)
        # The LSTM is stateful;  manually reset the state of the network at the end of each training epoch
        model.reset_states()  # clears only the hidden states of your network

        # save fit errors
        fit_history['loss'].append(result.history['loss'])  # Now append the loss after the training to the list.
        fit_history['mse'].append(result.history['mean_squared_error'])
        fit_history['mae'].append(result.history['mean_absolute_error'])
        fit_history['mape'].append(result.history['mean_absolute_percentage_error'])

    fit_history['title'] = "num_in:" + str(num_in) + ' num_out:' + str(num_out) + " num_neurons:" + str(num_neurons)
    # print(fit_history)
    print("Training completed")

    return model, fit_history


def plot_fit_error(fit_history, label=''):
    # plt.plot(fit_history['loss'], label='loss')
    plt.plot(fit_history['mse'], label='mse' + label)
    # plt.plot(fit_history['mae'], label='mae')
    # plt.plot(fit_history['mape'], label='mape')


def save_fit_plot(name, temp_data_folder):
    plt.legend()
    plt.savefig(temp_data_folder+"fit_history "+str(datetime.datetime.now().strftime("%Y-%m-%d %H %M"))+" "+name+".png")



def build_mutliple_steps_model(train_x, train_y, temp_data_folder, num_neurons, num_epochs):
    # build a full model
    model, fit_history = build_model(train_x, train_y, num_neurons, num_epochs)

    # plot model fit history
    plt.figure()
    plot_fit_error(fit_history)
    plt.title(fit_history['title'])
    save_fit_plot('step_multiple', temp_data_folder)

    # save model
    k_utils.save_model(model, temp_data_folder)


def build_one_step_model(train_x, train_y, temp_data_folder, num_neurons, num_epochs, step_range=None):
    if step_range is None:
        num_output = train_y.shape[1]
        step_range = range(0, num_output)
    plt.figure()
    for step in step_range:
        step_text = ' step_' + str(step)
        print("build model for "+step_text)

        train_y_step = train_y[:, (step-1)]
        train_y_step = train_y_step.reshape(train_y.shape[0], 1)
        model, fit_history = build_model(train_x, train_y_step, num_neurons, num_epochs)
        # plot model fit history
        k_utils.save_model(model, temp_data_folder + 'step_' + str(step) + '_')
        plot_fit_error(fit_history, step_text)

    plt.legend()
    plt.title(fit_history['title'])
    save_fit_plot(step_text, temp_data_folder)


#--------------------------------------------

def xx(model, train_x, train_y):
    num_in = train_x.shape[1]
    predicted_y = np.array([])
    for ix in range(len(train_x)):
        predicted = model.predict(train_x[ix].reshape(1, 1, num_in))
        predicted_y = np.append(predicted_y, predicted)

    predicted_y = predicted_y.reshape(train_y.shape[0], train_y.shape[1])

    rmse = math.sqrt(mean_squared_error(train_y, predicted_y))
    print('Test RMSE: %.3f' % rmse)
