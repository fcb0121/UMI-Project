FROM osrf/ros:noetic-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
SHELL ["/bin/bash", "-lc"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    build-essential \
    cmake \
    doxygen \
    git \
    ipython3 \
    libblas-dev \
    libboost-all-dev \
    libeigen3-dev \
    liblapack-dev \
    libopencv-dev \
    libpoco-dev \
    libsuitesparse-dev \
    libtbb-dev \
    libv4l-dev \
    nano \
    python3-catkin-tools \
    python3-dev \
    python3-igraph \
    python3-matplotlib \
    python3-opencv \
    python3-osrf-pycommon \
    python3-pip \
    python3-pyx \
    python3-scipy \
    python3-tk \
    python3-wxgtk4.0 \
    ros-noetic-cv-bridge \
    ros-noetic-image-transport \
    ros-noetic-rosbag \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /kalibr_workspace/src \
    && cd /kalibr_workspace/src \
    && git clone https://github.com/ethz-asl/kalibr.git \
    && source /opt/ros/${ROS_DISTRO}/setup.bash \
    && cd /kalibr_workspace \
    && catkin init \
    && catkin config --extend /opt/ros/${ROS_DISTRO} \
    && catkin config --merge-devel \
    && catkin config --cmake-args -DCMAKE_BUILD_TYPE=Release \
    && catkin build -DCMAKE_BUILD_TYPE=Release -j2

RUN printf '%s\n' \
    'source /opt/ros/noetic/setup.bash' \
    'source /kalibr_workspace/devel/setup.bash' \
    > /etc/profile.d/kalibr.sh

WORKDIR /data
CMD ["/bin/bash"]
