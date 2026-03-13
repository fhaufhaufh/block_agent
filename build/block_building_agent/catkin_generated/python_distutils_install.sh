#!/bin/sh

if [ -n "$DESTDIR" ] ; then
    case $DESTDIR in
        /*) # ok
            ;;
        *)
            /bin/echo "DESTDIR argument must be absolute... "
            /bin/echo "otherwise python's distutils will bork things."
            exit 1
    esac
fi

echo_and_run() { echo "+ $@" ; "$@" ; }

echo_and_run cd "/home/ytm/block_agent/src/block_building_agent"

# ensure that Python install destination exists
echo_and_run mkdir -p "$DESTDIR/home/ytm/block_agent/install/lib/python3/dist-packages"

# Note that PYTHONPATH is pulled from the environment to support installing
# into one location when some dependencies were installed in another
# location, #123.
echo_and_run /usr/bin/env \
    PYTHONPATH="/home/ytm/block_agent/install/lib/python3/dist-packages:/home/ytm/block_agent/build/block_building_agent/lib/python3/dist-packages:$PYTHONPATH" \
    CATKIN_BINARY_DIR="/home/ytm/block_agent/build/block_building_agent" \
    "/home/ytm/anaconda3/envs/ytm_space/bin/python3" \
    "/home/ytm/block_agent/src/block_building_agent/setup.py" \
    egg_info --egg-base /home/ytm/block_agent/build/block_building_agent \
    build --build-base "/home/ytm/block_agent/build/block_building_agent" \
    install \
    --root="${DESTDIR-/}" \
    --install-layout=deb --prefix="/home/ytm/block_agent/install" --install-scripts="/home/ytm/block_agent/install/bin"
