""" Showing an image on the screen in parallel to the main program, and update the shown image on the screen
    from the other thread.
"""

from __future__ import print_function, division, absolute_import

import numpy as np
import time
import multiprocessing

from PIL import Image
from PIL import ImageTk
from PIL import ImageFont
from PIL import ImageDraw

# tkinter import that works on both Python 2 and 3
try:
    import tkinter
except:
    import Tkinter as tkinter


try:
    from mem_top import mem_top
    USE_MEMTOP = True
except:
    USE_MEMTOP = False


def drawText(img, img_text):
    """ Draws text on the image represented as a numpy array.

    """

    # Construct a PIL draw object
    draw = ImageDraw.Draw(img)

    # Load the default font
    font = ImageFont.load_default()

    # Draw the text on the image, in the upper left corner (green text)
    draw.text((0, 0), img_text, (0,155,62), font=font)
    draw = ImageDraw.Draw(img)

    # # Convert the type of the image to grayscale, with one color
    # img = img.convert('L')

    return img



class LiveViewer(multiprocessing.Process):
    """ Uses OpenCV to show an image, which can be updated from another thread. """

    def __init__(self, config, window_name=None):
        """
        Keyword arguments:
            window_name: [str] name (title) of the window

        """

        super(LiveViewer, self).__init__()
        
        self.config = config
        self.img_queue = multiprocessing.Queue()
        self.window_name = window_name
        self.run_exited = multiprocessing.Event()
        
        self.imagesprite = ""



        self.start()



    def start(self):
        """ Start the live viewer window.
        """

        super(LiveViewer, self).start()



    def updateImage(self, img, img_text=None):
        """ Update the image on the screen. 
        
        Arguments:
            img: [ndarray] array with the image
            img_text: [str] text to be written on the image
            
        """

        self.img_queue.put([img, img_text])

        time.sleep(0.1)


    def getImage(self):

        # Get the next element in the queue (blocking, until next element is available)
        item = self.img_queue.get(block=True)

        # If the 'poison pill' is received, exit the viewer
        if item is None:
            self.run_exited.set()
            return


        img, img_text = item

        # Convert the image from numpy array to PIL image
        image = Image.fromarray(np.uint8(img))
        image = image.convert('RGB')
        
        # Get screen size
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        

        # If the screen is smaller than the image, resize the image
        if (screen_h < img.shape[0]) or (screen_w < img.shape[1]):

            # Find the ratios between dimentions
            y_ratio = screen_h/img.shape[0]
            x_ratio = screen_w/img.shape[1]

            # Resize the image so that the image fits the screen
            min_ratio = min(x_ratio, y_ratio)

            width_new = int(img.shape[1]*min_ratio)
            height_new = int(img.shape[0]*min_ratio)

            # Set the new window geometry
            self.root.geometry('{:d}x{:d}'.format(width_new, height_new))

            # Resize the image
            image = image.resize((width_new, height_new), Image.ANTIALIAS)



        # Write text on the image if any is given
        if img_text is not None:
            image = drawText(image, img_text)


        # This has to be assigned to 'self', otherwise the data will get garbage collected and not shown
        #   on the screen
        self.image_tkphoto = ImageTk.PhotoImage(image)




        # Log memory
        if USE_MEMTOP:
            log.debug(mem_top())


        # Delete the old image
        self.canvas.delete(self.imagesprite)

        # Create an image window
        self.imagesprite = self.canvas.create_image(0, 0, image=self.image_tkphoto, anchor='nw')

        # Repeat the image update
        if not self.run_exited.is_set():
            self.canvas.after(100, self.getImage)



    def run(self):
        """ Keep updating the image on the screen from the queue. """


        # Init the window
        self.root = tkinter.Tk()

        # Position window in the upper left corner
        self.root.geometry('+0+0')

        # Set window title
        self.root.title('Maxpixel')

        # Disable closing the window
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self.canvas = tkinter.Canvas(self.root, width=self.config.width, height=self.config.height)
        self.canvas.pack()
        self.canvas.configure(background='black')

        self.getImage()

        self.root.mainloop()


        # while not self.run_exited.is_set():
        #     time.sleep(0.1)


        # Close the window
        if self.root is not None:
            self.root.withdraw()
            self.root.destroy()
            del self.root



    def stop(self):
        """ Stop the viewer. """

        self.terminate()

        self.join()




if __name__ == "__main__":

    import RMS.ConfigReader as cr

    ### Test the live viewer ###

    # Load the default configuration file
    config = cr.parse(".config")

    # Test resizing
    config.width = 2000
    config.height = 2000

    # Start the viewer
    live_view = LiveViewer(config, window_name='Maxpixel')

    # Generate an example image
    img = np.zeros((config.height, config.width))

    for i in range(100):
        i = i*3
        img[i:i+2, i:i+2] = 255
        live_view.updateImage(img, str(i))
        time.sleep(0.1)



    # img[::5, ::5] = 128

    # # Update the image in the Viewer
    # live_view.updateImage(img.astype(np.uint8), 'test 1')

    # print('updated')

    # time.sleep(5)

    # # Generate another image
    # img[::-2, ::-2] = 128

    # # Upate the image in the viewer
    # live_view.updateImage(img, 'blah 2')

    # time.sleep(2)

    # print('close')



    # Stop the viewer
    live_view.stop()
    del live_view # IMPORTANT! Otherwise the program does not exit

    print('stopped')