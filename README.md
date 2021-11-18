# Overview

This is a hobby project which includes a hand-gesture controlled virtual piano using an android phone camera and some OpenCV library functions. My motivation to initiate this project is two fold. I always felt the urge to be able to play piano since my childhood but huge instrumental costs barred my way. This is true for most of the musical instruments which are often very costly. I thought of putting my recently acquired computer vision skills to practice and make virtual music instruments through this project. Currently, this project only supports piano but I shall add modules for other instruments soon. While this project is very basic, more contributions are always welcomed to further improve it. 

## Working

This project employs use of many other libraries apart from OpenCV such as pygame, mediapipe etc to develop it. In the first step, we use mediapipe (add link) library to detect 21 finger landmarks for each hand. MediaPipe offers open source cross-platform, customizable ML solutions for object detection, face detection, human pose detection/tracking etc, and is one of the most widely used libraries for hand motion tracking. Once all finger landmarks are obtained, we use a simple algorithm to detect a particular key press. If key press is within the boundaries of virtual piano, we add that piano key music to a list and start playing it. The algorithm is capable of mixing up several key notes simultaneously in case of multiple key presses. Interesting, isn't it? So let's dive in and get it started on your own PC!

## Getting Started

- As with any other project, we will first install all the dependencies required for building this project which are listed down in the requirements.txt file. To install, use `pip3 install' command as shown below:

` pip3 install -r requirements.txt`

  Note that python 2 users should use pip instead of pip3. If any dependencies couldn't be installed on your system due to compatibility issues, please search for other compatible versions!

- Once dependencies are installed, it is time to clone the repository using `git clone` and change to `~/scripts` directory. Use the following command.

`git clone https://github.com/AbhinavGupta121/Virtual-Piano-using-Open-CV.git`
`cd Virtual-Piano-using-Open-CV/scripts/`

- Now it is time to install 88 piano key sounds. You can simply download them manually using this (link) or by using command line itself. To use command line, run this command under `~/scripts` folder.

`wget https://archive.org/download/25405-tedagame-88-piano-keys-long-reverb/25405__tedagame__88-piano-keys-long-reverb.zip`

Now extract the zip file and you are good to go!

- 



