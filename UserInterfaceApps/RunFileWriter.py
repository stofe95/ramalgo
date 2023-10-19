import numpy as np
import h5py
from datetime import datetime
import os

from PhotostimulatorTool import PhotostimulatorTool


class RunFileWriter:
    CSV_EXTENSION = '.csv'
    AVI_EXTENSION = '.avi'
    #MP4_EXTENSION = '.mp4'
    HDF5_EXTENSION = '.hdf5'

    OPENFILEDIALOG_FILETYPES = (('Test Files', ['*.avi', '*.csv']), ('HDF5 Files', ['*.hdf5']), ('All types', '*.*'))

    # output the data filename in the following format
    @staticmethod
    def format_datafilename(filename, mouse_id, trial_id, file_ext):
        result = {}

        # AVI file:
        # [filename]_mouse[mouse_id]_trial[trial_id].avi
        if file_ext == RunFileWriter.AVI_EXTENSION:
            result['video_file'] = filename + '_mouse' + str(mouse_id) + '_trial' + str(trial_id) + file_ext

        # CSV file:
        # [filename]_mouse[mouse_id]_trial[trial_id]_wave.csv
        # [filename]_mouse[mouse_id]_trial[trial_id]_tracking.csv
        elif file_ext == RunFileWriter.CSV_EXTENSION:
            result['waveform_file'] = filename + '_mouse' + str(mouse_id) + '_trial' + str(trial_id) + '_wave' + file_ext
            result['tracking_file'] = filename + '_mouse' + str(mouse_id) + '_trial' + str(trial_id) + '_tracking' + file_ext

        # HDF5 file:
        # trial[trial_id]_wave
        # trial[trial_id]_tracking
        # trial[trial_id]_substage_frame_times
        elif file_ext == RunFileWriter.HDF5_EXTENSION:
            result['waveform_dataset'] = 'trial' + str(trial_id) + '_wave'
            result['tracking_dataset'] = 'trial' + str(trial_id) + '_tracking'
            result['frametimes_dataset'] = 'trial' + str(trial_id) + '_substage_frame_times'

        return result

    # save trial(s) as an HDF5 file
    # /
    # mouseF1
    #     trial1 (metadata: datetime)
    #         trial1_wave (metadata: wave parameters)
    #         trial1_tracking
    #         trial1_frame_times
    #     trial2 (metadata: datetime)
    #         trial2_wave (metadata: wave parameters)
    #         trial2_tracking
    #         trial2_frame_times
    #     ...
    # mouseF2
    # ...
    # exceptions: wave_data is None
    @staticmethod
    def save_HDF5(selected_folder, filename, mouse_id, trial_id, trial_datetime, wave_settings, wave_data, tracking_data=None, substage_frame_times=None, good_trial=1, comment='',videopath=None, hsv_params=None):
        filepath = selected_folder + '\\' + filename + RunFileWriter.HDF5_EXTENSION

        # create HDF5 file, r/w if exists
        with h5py.File(filepath, 'a') as hdf5:
            # create a group for the given mouse, open if exists
            mouse_group = hdf5.require_group('mouse' + str(mouse_id))

            # create a group for the given trial id, open if exists
            trial_group = mouse_group.require_group('trial' + str(trial_id))
            trial_group.attrs.create('num',trial_id,dtype=int)
            trial_group.attrs.create('good_trial',good_trial,dtype=int)
            trial_group.attrs.create('comment',comment,dtype=str('a' + str(len(comment))))
            if hsv_params:
                trial_group.attrs.create('hsv_fps',hsv_params['FPS'],dtype=int)
                trial_group.attrs.create('hsv_length',hsv_params['length'],dtype='f')
                trial_group.attrs.create('hsv_filename',hsv_params['filename'],dtype=str('a' + str(len(hsv_params['filename']))))


            # create metadata, overwrite if exists
            # trial group metadata: datetime
            trial_datetime = trial_datetime.strftime("%Y-%m-%d %H:%M:%S")
            trial_group.attrs.create('timestamp', trial_datetime, dtype=str('a' + str(len(trial_datetime))))

            # create datasets for each trial, overwrite if exists
            dataset_names = RunFileWriter.format_datafilename(filename, mouse_id, trial_id, RunFileWriter.HDF5_EXTENSION)

            waveform_dataset = None
            wave_exists = False
            waveform_datafilename = dataset_names['waveform_dataset']
            tracking_dataset = None
            tracking_exists = False
            tracking_datafilename = dataset_names['tracking_dataset']
            substage_frame_times_dataset = None
            frame_times_exists = False
            frame_times_datafilename = dataset_names['frametimes_dataset']

            for key in trial_group.keys():
                if key == waveform_datafilename:
                    wave_exists = True
                elif key == tracking_datafilename:
                    tracking_exists = True
                elif key == frame_times_datafilename:
                    frame_times_exists = True

            # waveform data
            # red/blue: [0] = blue, [1] = red
            # red/green/laser: [0] = green, [1] = laser, [2] = red
            wave_config = wave_settings['mode']
            if wave_config == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
                receive_blue = wave_data['blue']
                receive_red = wave_data['red']

                if wave_exists:
                    waveform_dataset = trial_group[waveform_datafilename]
                    waveform_dataset.resize(2, axis=0)
                    waveform_dataset.resize(receive_blue.size, axis=1)
                    # clear existing metadata
                    waveform_dataset.attrs.clear()
                else:
                    waveform_dataset = trial_group.create_dataset(waveform_datafilename, (2, receive_blue.size), dtype='f', maxshape=(3, None))

                waveform_dataset[0] = receive_blue
                waveform_dataset[1] = receive_red

                # waveform data metadata: parameters
                for param in wave_settings.keys():
                    if isinstance(wave_settings[param], str):
                        waveform_dataset.attrs.create(param, wave_settings[param], dtype=str('a' + str(len(wave_settings[param]))))
                    elif isinstance(wave_settings[param], float):
                        waveform_dataset.attrs.create(param, wave_settings[param], dtype='f')

            elif wave_config == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
                receive_green = wave_data['green']
                receive_laser = wave_data['laser']
                receive_red = wave_data['red']

                if wave_exists:
                    waveform_dataset = trial_group[waveform_datafilename]
                    waveform_dataset.resize(3, axis=0)
                    waveform_dataset.resize(receive_green.size, axis=1)
                    # clear existing metadata
                    waveform_dataset.attrs.clear()
                else:
                    waveform_dataset = trial_group.create_dataset(waveform_datafilename, (3, receive_green.size), dtype='f', maxshape=(3, None))

                waveform_dataset[0] = receive_green
                waveform_dataset[1] = receive_laser
                waveform_dataset[2] = receive_red

                # waveform data metadata: parameters
                for param in wave_settings.keys():
                    if isinstance(wave_settings[param], str):
                        waveform_dataset.attrs.create(param, wave_settings[param], dtype=str('a' + str(len(wave_settings[param]))))
                    elif isinstance(wave_settings[param], float):
                        waveform_dataset.attrs.create(param, wave_settings[param], dtype='f')

            # video frame times
            if substage_frame_times:
                if frame_times_exists:
                    substage_frame_times_dataset = trial_group[frame_times_datafilename]
                    substage_frame_times_dataset.resize(len(substage_frame_times), axis=1)
                else:
                    substage_frame_times_dataset = trial_group.create_dataset(frame_times_datafilename, (1, len(substage_frame_times)), dtype='f8', maxshape=(1, None))
                if videopath:
                    substage_frame_times_dataset.attrs.create('path',videopath,dtype=str('a' + str(len(videopath))))

                substage_frame_times_dataset[:] = substage_frame_times

            # tracking data
            # data[i] = [time, xerror, xvelocity, yerror, yvelocity]
            if type(tracking_data) is np.ndarray:
                if tracking_exists:
                    tracking_dataset = trial_group[tracking_datafilename]
                    tracking_dataset.resize(tracking_data.shape[0], axis=0)
                else:
                    tracking_dataset = trial_group.create_dataset(tracking_datafilename, tracking_data.shape, dtype='f', maxshape=(None, tracking_data.shape[1]))

                tracking_dataset[:] = tracking_data

            '''
            frames = self.__videocapture.get_last_savedframes()
            dataset_shape = (len(frames), frames[0].shape[0], frames[0].shape[1], frames[0].shape[2])
            #chunks = (1, frames[0].shape[0]/10, frames[0].shape[1]/10, frames[0].shape[2])
            video_dataset = mouse_group.create_dataset('trial' + str(trial_id) + '_video_v' + str(version), dataset_shape, dtype='u8', chunks=True, compression='gzip', compression_opts=4)
            video_dataset[:] = frames
            '''

    # save one trial as a .csv file
    # exceptions: wave_data is None
    @staticmethod
    def save_csv(selected_folder, filename, mouse_id, trial_id, wave_config, wave_data, tracking_data=None):
        filenames = RunFileWriter.format_datafilename(filename, mouse_id, trial_id, RunFileWriter.CSV_EXTENSION)
        waveform_filename = filenames['waveform_file']
        tracking_filename = filenames['tracking_file']

        # waveform data
        # red/blue: Blue,Red
        # red/green/laser: Green,LASER,Red
        # TODO: assumes sampling rate 1000 Hz
        if wave_config == PhotostimulatorTool.REDBLUE_CONFIG_NAME or wave_config == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            save_path = selected_folder + '\\' + filename + '_csv_data'
            if not os.path.exists(save_path):
                os.mkdir(save_path)
            filepath = save_path + '\\' + waveform_filename
            with open(filepath, 'w') as f:
                if wave_config == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
                    receive_blue = wave_data['blue']
                    receive_red = wave_data['red']

                    f.write('Blue,Red\n')
                    for i in range(receive_blue.size):
                        f.write(','.join([str(receive_blue[i]), str(receive_red[i])]) + '\n')

                elif wave_config == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
                    receive_green = wave_data['green']
                    receive_laser = wave_data['laser']
                    receive_red = wave_data['red']

                    f.write('Green,LASER,Red\n')
                    for i in range(receive_green.size):
                        f.write(','.join([str(receive_green[i]), str(receive_laser[i]), str(receive_red[i])]) + '\n')

        # tracking data
        # Time,XError,XVelocity,YError,YVelocity
        if type(tracking_data) is np.ndarray:
            filepath = selected_folder + '\\' + tracking_filename
            with open(filepath, 'w') as f:
                f.write('Time,XError,XVelocity,YError,YVelocity\n')
                for i in range(tracking_data.shape[0]):
                    row = []
                    for j in range(tracking_data.shape[1]):
                        row.append(str(tracking_data[i][j]))
                    f.write(','.join(row) + '\n')

    @staticmethod
    def get_hdf5_info(selected_folder, filename, mouse_id):
        if not(selected_folder):
            return None, None
        filepath = selected_folder + '\\' + filename + RunFileWriter.HDF5_EXTENSION

        # create HDF5 file, r/w if exists
        try:
            with h5py.File(filepath, 'r') as hdf5:
                    mouse = hdf5['mouse' + str(mouse_id)]
                    trials = list(mouse.values())
                    if len(trials) < 1:
                        return None, None


                    max = (0, 0)
                    for trial in trials:
                        trial_num = trial.attrs['num']
                        trial_datetime = trial.attrs['timestamp']
                        trial_datetime = trial_datetime.decode('utf-8')
                        if trial_num > max[0]:
                            max = (trial_num,trial_datetime)
                    return max
        except (KeyError,OSError):
                return None, None