from time import monotonic, sleep
from pyscript.core.utils.decorators import immutable, inheritable, singleton

@singleton
@immutable
@inheritable
class FPSTimer:

    __slots__ = ()

    _lastTick = 0.0
    _timeElapsed = 0.0
    _rawTime = 0.0
    _framesPerSecond = 0.0

    def __new_singleton__(cls):
        global fpstimer
        fpstimer = super(cls, cls).__new__(cls)
        return fpstimer

    def tick(self, framerate):
        currentTime = monotonic()
        lastTick = FPSTimer._lastTick
        elapsedTime = currentTime - lastTick

        if framerate > 0:
            minFrameTime = 1 / framerate
            if elapsedTime < minFrameTime:
                sleep(minFrameTime - elapsedTime)

        currentTime = monotonic()

        FPSTimer._framesPerSecond = 0.0 if currentTime == lastTick else 1 / (currentTime - lastTick)
        FPSTimer._timeElapsed = timeElapsed = currentTime - lastTick
        FPSTimer._rawTime = elapsedTime
        FPSTimer._lastTick = currentTime

        return timeElapsed

    def get_time(self):
        return FPSTimer._timeElapsed

    def get_rawtime(self):
        return FPSTimer._rawTime

    def get_fps(self):
        return FPSTimer._framesPerSecond

    getTime = get_time
    getRawTime = get_rawtime
    getFPS = get_fps

FPSTimer()