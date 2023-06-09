import os
import platform
from pytube import YouTube


class YouTubeHelper:
    """ Class to download a YouTube video from a given url
    """
    url = None
    filepath_video = None
    media_title = None

    def __init__(self, url):
        """ Constructor for the YouTubeVideo class

        Args:
            url (str): The url of the YouTube video

        Raises:
            Exception: Thrown if the given url is invalid
        """
        yt = YouTube(url)
        try:
            yt.check_availability()
            self.url = url
        except:
            raise Exception("Invalid video URL")

    def download(self, filename):
        """ Method to download the video from the given url
        """
        yt = YouTube(self.url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()

        if platform.system() == "Windows" or platform.system() == "MacOS":
            filepath_video = os.getcwd() + "/app/downloads/"
        else:
            filepath_video = "/home/jan/wwwroot/gruettechat/gruettechat/app/downloads/"
        stream.download(filename=f"{filename}.mp4", output_path=filepath_video)

        self.filepath_video = filepath_video
        self.media_title = yt.title

    def get_filepath_video(self):
        """ Method to get the filepath of the downloaded video

        Returns:
            str: The filepath of the downloaded video (None if the video has not been downloaded yet)
        """
        return self.filepath_video

    def get_media_title(self):
        """ Method to get the media title

        Returns:
            str: The filepath of the media title (None if no video has been downloaded yet)
        """
        return self.media_title


if __name__ == "__main__":
    """ Main method downloads a YouTube video from a given url and converts it to into an mp3 file
    """
    while True:
        url = input("Enter the url of the video:\n")
        try:
            yt = YouTube(url)
            break
        except Exception as e:
            print(e)

    video = YouTubeHelper(url)
    video.download()
    video.mp4_to_mp3()
