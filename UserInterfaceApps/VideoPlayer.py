import PIL.Image, PIL.ImageTk
import cv2
import threading


class VideoPlayer:
    def __init__(self, camera_label):
        self.__camera_label = camera_label
        # TODO: get fps from some metadata (currently based on UserInterface.__delay)
        self.__delay = 15
        self.__photos = []
        self.__video_capture = None
        self.__photo = None
        self.__paused = False

        self.__playback_thread = None

    # exceptions: invalid video file, failed to open file
    def load(self, video_file_path):
        if not video_file_path:
            raise Exception('No video file path given to open.')

        # note: close other connections to video file for video capture to open connection
        self.__video_capture = cv2.VideoCapture(video_file_path, cv2.CAP_FFMPEG)
        if not self.__video_capture.isOpened():
            raise Exception("Failed to open video file.")

        # show first frame
        ret, frame = self.get_frame()
        if ret:
            self.__photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.__camera_label.config(image=self.__photo)

    def get_frame(self):
        if self.__video_capture.isOpened():
            ret, frame = self.__video_capture.read()
            if ret:
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return ret, None
        return None, None

    def loop_video(self):
        if self.__video_capture and not self.__photos:
            while self.__video_capture.isOpened():
                ret, frame = self.get_frame()
                if ret:
                    self.__photos.append(PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame)))
                else:
                    break

        for photo in self.__photos:
            self.__camera_label.after(self.__delay, self.show_frame(photo))

    def show_frame(self, photo):
        self.__camera_label.config(image=photo)

    def play(self):
        if self.__playback_thread is not None:
            self.__playback_thread.join()
        self.__playback_thread = threading.Thread(target=self.loop_video, daemon=True)
        self.__playback_thread.start()

    # TODO: implement
    def pause(self):
        pass

    def __del__(self):
        if self.__video_capture.isOpened():
            self.__video_capture.release()
            cv2.destroyAllWindows()