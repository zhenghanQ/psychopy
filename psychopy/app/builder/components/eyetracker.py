# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from ._base import BaseComponent, Param

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'eyetracker.png')
tooltip = _translate('Eyetracker: use one of several eyetrackers to follow '
                     'gaze')


class EyetrackerComponent(BaseComponent):
    """A class for using one of several eyetrackers to follow gaze"""
    categories = ['Responses']

    def __init__(self, exp, parentName, name='eyes',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 save='final', configFile='myTracker.yaml'):
        self.type = 'Eyetracker'
        self.url = "http://www.psychopy.org/builder/components/eyetracker.html"
        self.parentName = parentName
        self.exp = exp  # so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['iohub'])
        # params
        self.params = {}
        self.order = ['Config file']  # first param after the name

        # standard params (can ignore)
        msg = "Name of this component (alpha-numeric or _, no spaces)"
        self.params['name'] = Param(
            name, valType='code', allowedTypes=[],
            hint=_translate(msg),
            label="Name")

        self.params['startType'] = Param(
            startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint=_translate("How do you want to define your start point?"))

        self.params['stopType'] = Param(
            stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)',
                         'frame N', 'condition'],
            hint=_translate("How do you want to define your end point?"))

        self.params['startVal'] = Param(
            startVal, valType='code', allowedTypes=[],
            hint=_translate("When does the component start?"))

        self.params['stopVal'] = Param(
            stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("When does the component end? (blank is endless)"))

        msg = "(Optional) expected start (s), purely for representing in the timeline"
        self.params['startEstim'] = Param(
            startEstim, valType='code', allowedTypes=[],
            hint=_translate(msg))

        msg = "(Optional) expected duration (s), purely for representing in the timeline"
        self.params['durationEstim'] = Param(
            durationEstim, valType='code', allowedTypes=[],
            hint=_translate(msg))

        # useful params for the eyetracker - keep to a minimum if possible! ;-)
        self.params['Config file'] = Param(
            configFile, valType='str',
            hint=_translate("How do you want to define your start point?"))

        msg = "How often should the eyetracker state (x,y,pupilsize...) be stored? On every video frame, every click or just at the end of the Routine?"
        self.params['saveState'] = Param(
            save, valType='str',
            allowedVals=['final', 'every frame', 'never'],
            hint=_translate(msg),
            label="Save eyetracker state")

    def writePreWindowCode(self, buff):
        buff.writeIndented("#%(name)s: do calibration\n" % self.params)

        # these might move to a more general place later, when we're always
        # planning on having iohub running
        buff.writeIndented("io_config = iohub.load(file(%('Config file')s,'r'), Loader=iohub.Loader)\n" % self.params)
        buff.writeIndented("io = iohub.ioHubConnection(io_config)\n")
        buff.writeIndented("eyetracker = io.getDevice('tracker')\n" % self.params)
        buff.writeIndented("eyetracker.runSetupProcedure()\n" % self.params)

    def writeInitCode(self, buff):
        pass  # do we need anything after window creation but before run starts?

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        # create some lists to store recorded values positions and events if we
        # need more than one
        buff.writeIndented("# setup some python lists for storing info about the %(name)s\n" % self.params)
        # a list of vals for each val, rather than a scalar
        if self.params['saveState'].val in ['every frame', 'on click']:
            buff.writeIndented("%(name)s.x = []\n" % self.params)
            buff.writeIndented("%(name)s.y = []\n" % self.params)
            # is this common or is Jon making it up?!
            buff.writeIndented("%(name)s.pupil = []\n" % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # test for whether we're just starting to record
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)
        buff.writeIndented("#clear events and start tracking\n")
        buff.writeIndented("io.clearEvents('all')\n")
        buff.writeIndented("%(name)s.setRecordingState(True)\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = STOPPED\n" % self.params)
            buff.writeIndented("%(name)s.setRecordingState(False)\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # if STARTED and not STOPPED!
        buff.writeIndented("if %(name)s.status == STARTED:  # only update if started and not stopped!\n" % (self.params))
        buff.setIndentLevel(1, relative=True)  # to get out of the if statement
        dedentAtEnd = 1  # keep track of how far to dedent later
        buff.writeIndented("%(name)s.x, %(name)s.y = eyetracker.getPosition()\n" % (self.params))
        buff.writeIndented("%(name)s.pupil = eyetracker.getPupilSize()\n" % (self.params))

        # actual each-frame checks
        if self.params['saveState'].val in ['every frame']:
            buff.writeIndented("x, y = eyetracker.getPosition()\n" % (self.params))
            buff.writeIndented("%(name)s.x.append(x)\n" % (self.params))
            buff.writeIndented("%(name)s.y.append(y)\n" % (self.params))
            buff.writeIndented("%(name)s.pupil.append(eyetracker.getPupilSize())\n" % (self.params))

        # dedent
        # 'if' statement of the time test and button check
        buff.setIndentLevel(-dedentAtEnd, relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name'].val
        # do this because the param itself is not a string!
        store = self.params['saveState'].val
        # check if we're in a loop (so saving is possible)
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = None

        # if store=='final' then update value
        if store == 'final' and currLoop != None:
            buff.writeIndented("# get info about the %(name)s\n" % self.params)
            buff.writeIndented("%(name)s.x, %(name)s.y = eyetracker.getPosition()\n" % self.params)
            buff.writeIndented("x, y = %(name)s.getPos()\n" % self.params)
            buff.writeIndented("%(name)s.pupil = eyetracker.getPupilSize()\n" % self.params)
        # then push to psychopy data file if store='final','every frame'
        if store != 'never' and currLoop != None:
            buff.writeIndented("# save %(name)s data\n" % self.params)
            for property in ['x', 'y', 'pupil']:
                buff.writeIndented(
                    "%s.addData('%s.%s', %s.%s)\n" %
                    (currLoop.params['name'], name, property, name, property))

        # make sure eyetracking stops recording (in case it hsn't stopped
        # already)
        buff.writeIndented("eyetracker.setRecordingState(False)\n")

    def writeExperimentEndCode(self, buff):
        buff.writeIndented("eyetracker.setConnectionState(False)\n")
        # in future this should be done generally, not by the eyetracker
        buff.writeIndented("io.quit()\n")
