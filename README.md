# WORK WORK BACK TO WORK
![image of two "BACK TO WORK" timers back-to-back. one is marked "WORKS". the other is marked "DOES NOT WORK".](https://github.com/workworklinux/workwork/assets/155671658/b66c0674-daf0-4d38-adc7-b1263dbc34ae)
![image of the working timer's menu open. "Empty Program Slots" is highlighted, marked "ONE NEW BUTTON!!"](https://github.com/workworklinux/workwork/assets/155671658/dcd944b3-0b3f-41e1-b93d-839b29a658b3)

"cross-platform" python port of neil cicerega's WORK TIMER. rough aesthetic accuracy with a few minor new features. tested on linux mint 21.2, should work on any. mac may only work if run as root due to pynput library limitations.

## installation
install required pip libraries, clone repo and run
```bash
pip install wxpython pyyaml pynput
git clone https://github.com/workworklinux/workwork.git
cd workwork
python3 workwork.py
```
configuration yaml files are stored in ~/.workwork/config.yaml. background and text color can be changed here as a bonus. 

## limitations
- probably doesn't work on a lot of shit but notably Fucked on wayland. everything here is x11 based. anyone willing to contribute go on ahead
- some applications [like krita] run temporary executables. these will not persist between program relaunches and will have to be re-selected.

### advantages
- works

## security
pynput is functionally a keylogger for all keyboard and mouse inputs. this is also the case for autohotkey [which is even more aggressive in intercepting system input] so it shouldn't be a concern to you unless you're Very Paranoid. the script never reads any key input the library could provide and everything is immediately thrown away as soon as "user activity has taken place" is verified.
