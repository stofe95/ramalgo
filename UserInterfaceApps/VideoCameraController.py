import cv2
import time
from datetime import datetime
import multiprocessing as mp
import queue
import os
from UserInterfaceApps.RunFileWriter import RunFileWriter

class FrameManipulator:
    @staticmethod
    def convert_BGR2RGB(frame):
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # show timestamp on frame
    @staticmethod
    def draw_timestamp(frame, timestamp):
        return cv2.putText(frame, str(timestamp), (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1, cv2.LINE_AA)

    # draw blue crosshair on frame
    @staticmethod
    def draw_crosshair(frame, position):
        return cv2.circle(frame, position, 10, (45, 227, 0), 2)


class VideoCameraController:
    # fps according to camera's resolution
    FPS = 30
    TARGET = (0.5, 0.5)

    # exceptions: on connection error
    def __init__(self, video_source=0):
        self.__video_source = video_source
        __videocapture = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
        ret, frame = VideoCameraController.get_frame(__videocapture)
        self.__width = int(__videocapture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.__height = int(__videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.target = (int(VideoCameraController.TARGET[0] * self.__width), int(VideoCameraController.TARGET[1] * self.__height))
        self.last_frame = frame
        if not ret:
            raise Exception("Failed to open camera")
        __videocapture.release()
        #frame_array = mp.Array('i',frame)
        #super().__init__()
        self.frame_queue = mp.Queue(maxsize=1)
        self.save_queue = mp.Queue(maxsize=1)
        self.frame_times_queue = mp.Queue(maxsize=1)
        self.__save_frame_queue = mp.Queue(maxsize=1)
        self.__save_frame_queue.put(False)
        self.run_process()

    def terminate(self):
        self.open = False

    def get_last_frame(self):
        if self.frame_queue.empty():
            return self.last_frame
        else:
            self.last_frame = self.frame_queue.get()
            return self.last_frame

    def run_process(self):
        self.proc = mp.Process(target=self.run,kwargs={
            'frame_queue':self.frame_queue,
            'save_queue':self.save_queue,
            'times_queue':self.frame_times_queue,
            'video_source':self.__video_source})
        self.proc.start()
    
    # start saving the acquired frames
    def start_video_recording(self):
        self.save_queue.put(True)

    # stop saving frames and write to .avi file
    def stop_video_recording(self, selected_folder, filename, mouse_id, trial_id, write_to_file=True):
        if write_to_file:
            abs_video_path = selected_folder + '/' + filename + '_videos'
            rel_video_path = './' + filename + '_videos'
            if not os.path.exists(abs_video_path):
                os.mkdir(abs_video_path)
            filenames = RunFileWriter.format_datafilename(filename, mouse_id, trial_id, RunFileWriter.AVI_EXTENSION)
            video_filename = filenames['video_file']
            filepath = rel_video_path + '/' + video_filename
            self.save_queue.put(abs_video_path + '/' + video_filename)
            return filepath
        else:
            return None
    
    def get_frame_times(self):
        return self.frame_times_queue.get()

    def run(self, frame_queue = None, save_queue = None, times_queue = None, video_source=0,target=(0.5,0.5)):

        # open video source
        __videocapture = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
        if not __videocapture.isOpened():
            raise Exception("Failed to open camera.")

        # default: 480p
        __width = int(__videocapture.get(cv2.CAP_PROP_FRAME_WIDTH))
        __height = int(__videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        __prev_frame_time = time.perf_counter()

        __frame_delay = 1.0 / VideoCameraController.FPS

        # Target position
        # target: Fraction of frame x,y dimensions to draw the crosshair and for autodetect to use for center
        __target_position = (int(__width*target[0]), int(__height*target[1]))
        save_fname = False
        saved_frames = []
        saved_frame_times = []
        while True:
            # delay according to camera fps
            if time.perf_counter() - __prev_frame_time >= __frame_delay:
                ret, frame = VideoCameraController.get_frame(__videocapture)
                if ret:

                    __prev_frame_time = time.perf_counter()

                    # draw on frame
                    #timestamp_frame = FrameManipulator.draw_timestamp(frame, datetime.now())
                    #target_frame = FrameManipulator.draw_crosshair(timestamp_frame, __target_position)

                    # frame must be RGB to display
                    #im_frame = FrameManipulator.convert_BGR2RGB(target_frame)

                    # display image
                    #self.__photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(im_frame))
                    
                    #The update rate of the camera is faster than the GUI is reading frames fromt he queue, so it will happen that 
                    #there is still a frame in the queue when the next frame is collected. In that case, check if the queue is full, (size =1)
                    #then if it is, get the frame in there and discard it so that we can put in the latest frame. If we don't use block=False
                    #then it does happen that we check that the queue is full and then in the time it takes to execute the next line, 
                    #the frame gets read by UserInterface and then we are stuck waiting to take out a frame that isn't there anymore.
                    #TODO use shared memory to pass frames rather than queue.
                    # This way VideoCameraController can just update the frames and UserInterface/MouseTrackingController can read the frames as they update
                    if frame_queue:
                        if frame_queue.full():
                            try:
                                frame_queue.get(block=False)
                            except queue.Empty:
                                pass
                            
                        frame_queue.put(frame)

                    #self.__camera_label.config(image=self.__photo)
                    #self.__camera_label.image = self.__photo

                    # save frame when recording
                    if not(save_queue.empty()):
                        save_fname = save_queue.get()
                        t0 = time.perf_counter()
                    if save_fname == True:
                        saved_frames.append(frame)
                        saved_frame_times.append(__prev_frame_time - t0)
                    elif len(saved_frames) > 0:
                        VideoCameraController.write_to_file(save_fname, saved_frames, saved_frame_times,__width,__height)
                        saved_frames.clear()
                        times_queue.put(saved_frame_times.copy())
                        saved_frame_times.clear()

                    
        
        self.finished=True

    # get the camera dimensions
    def get_frame_dims(self):
        return self.__width, self.__height

    # read one frame from the camera
    @staticmethod
    def get_frame(videocapture):
        # use lock to control video capture reads
        #with self.__getframe_lock:
        if videocapture.isOpened():
            ret, frame = videocapture.read()
            if ret:
                #frame = cv2.flip(frame,1)
                return ret, frame
            return ret, None
        return None, None

    # get the last recorded set of frames
    def get_last_savedframes(self):
        return self.__last_savedframes

    # get the last recorded set of frame times
    def get_last_frame_times(self):
        return self.__last_frame_times

    # save the frame
    def save_frame(self, frame, time):
        self.__savedframes.append(frame)
        self.__frame_times.append(time)

    # create a new video file (.avi or .mp4)
    @staticmethod
    def write_to_file(filename,__savedframes,__frame_times,__width,__height):
        if filename and __savedframes:


            # frame times start at 0
            __frame_times = [x - __frame_times[0] for x in __frame_times]

            # use fps calculated from saved frames
            arr = [j-i for i, j in zip(__frame_times[:-1], __frame_times[1:])]
            fps_avg = 1.0 / (sum(arr) / len(arr))
            print('Avg FPS: ',fps_avg)

            if '.avi' in filename:
                __out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'DIVX'), fps_avg, (__width, __height))
            elif '.mp4' in filename:
                __out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'mp4v'), fps_avg, (__width, __height))

            # output all saved frames to the created video file
            for frame in __savedframes:
                __out.write(frame)

            # close the video file, save a local record of the frames
            __out.release()

    def get_target(self):
        return self.__target_position

    def __del__(self):
        self.terminate()

        # if self.__videocapture.isOpened():
        #     self.__videocapture.release()
        # if self.__out:
        #     self.__out.release()
        cv2.destroyAllWindows()
        #super().__del__()