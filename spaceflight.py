import random
from xml.dom import minidom
import numpy as np
import vectorFunctions as vf

logLevel = 0

# Orbit class
class orbit:
    def __init__(self, name, top, height, colour):
        self.name = name
        self.top = top
        self.height = height
        self.colour = colour
        self.slots = []
        self.doc = minidom.Document()

    # Comparison function
    def __eq__(self, other):
        # Comparing with str
        if isinstance(other, str):
            return self.name == other
        # Comparing with another orbit object
        elif isinstance(other, orbit):
            return self.name == other.name

    # Function to draw background rectangles for each orbit.
    # The start and end x-axis positions are provided as parameters.
    # The y-axis is determined from the details of the orbit.
    def drawOrbitRectangle(self, svgparent, x1, x2):
        rect = self.doc.createElementNS("http://www.w3.org/2000/svg", "rect")
        rect.setAttribute("x", str(x1))
        rect.setAttribute("y", str(self.top))
        rect.setAttribute("width", str(x2 - x1))
        rect.setAttribute("height", str(self.height))
        rect.setAttribute("style", "fill:" + self.colour)
        svgparent.appendChild(rect)

    def addMission(self, newMission):
        newMission.orbit = self
        self.slots.append(newMission)
        newMission.slotIndex = len(self.slots) - 1
        if logLevel > 1:
            print("INFO: Mission " + newMission.name + " added to orbit " + self.name + " in slot " + str(
                newMission.slotIndex))

    def insertMission(self, newMission, index):
        self.slots.insert(index, newMission)
        newMission.orbit = self
        # Repair the slot references on this and the remaining missions as they are now pointing at the wrong place in the array.
        # Start at the position of the new mission, there is no need to repair the ones with lower indexes.
        orbL = len(self.slots)
        for i in range(index, orbL):
            self.slots[i].slotIndex = i

    # Remove mission (new style) removes mission and shunts all remaining missions up one place.
    def removeMission(self, exMission):
        if not(exMission.slotIndex is None) and not(exMission.orbit is None):
            try:
                # Remove element from the array.
                self.slots.remove(exMission)
            except ValueError:
                print("ERROR: Removing mission "
                      + exMission.name
                      + " from orbit "
                      + self.name
                      + ", mission not found in orbit slot")
            # Repair the slot references on the remaining missions as they are now pointing at the wrong place in the array.
            # Start at the position that old mission previously occupied, there is no need to repair the ones with lower indexes.
            orbL = len(self.slots)
            for i in range(exMission.slotIndex, orbL):
                self.slots[i].slotIndex = i
            if exMission.RV == 1:
                exMission.RV = 0  # Clear the RV flag on this mission.
            else:
                # Clear the RV flag on the mission that now occupies the slot previously occupied by the removed mission.
                # If it has an RV flag that means it was slaved to the mission we just removed and is now free.
                # Note that we only do this if the RV flag wasn't set on the removed mission. If it was it means there were multiple slaves to another master, the next mission is therefor still a slave.
                if len(self.slots) > exMission.slotIndex:
                    self.slots[exMission.slotIndex].RV = 0
            exMission.slotIndex = None  # ... and set the mission's slot index to null.
            exMission.orbit = None
        else:
            print("ERROR: Removing mission "
                  + exMission.name
                  + " from orbit "
                  + self.name
                  + ", mission not currently assigned to any orbit")

    def countRV(self):
        n = 0
        for slotMission in self.slots:
            if slotMission.RV == 1:
                n += 1
        return n

    def width(self):
        width = 0
        for slotMission in self.slots:
            width += slotMission.width()
        return width

    # Function to draw all the missions in an orbit
    # Calculates y-axis position to maintain even gaps between the missions.
    def draw(self, xPos):
        defaultGap = 30
        RVGap = 5
        maxSlip = 0
        thisSlip = 0
        slotsLen = len(self.slots)
        if (slotsLen > 0):
            offset = 0
            # Space available for variable gaps:
            # The total height of the orbit box
            availableSpace = self.height
            # Minus the combined width of all missions in this orbit
            availableSpace = availableSpace - self.width()
            # Minus the gaps between RVed missions (these are fixed and cannot change under any circumstances).
            availableSpace = availableSpace - self.countRV() * RVGap
            # The variable gap is the available space divided by the number of missions that are not in the RV state +1 (more gaps than missions).
            varGap = availableSpace / (slotsLen + 1 - self.countRV())
            if varGap > defaultGap:
                varGap = defaultGap
            for missionSlot in self.slots:
                if missionSlot.RV == 0:
                    offset += varGap
                else:
                    offset += RVGap
                halfWidth = missionSlot.width() / 2
                offset += halfWidth
                thisSlip = missionSlot.draw(xPos, offset + self.top)
                offset += halfWidth
                if thisSlip > maxSlip:
                    maxSlip = thisSlip
        return maxSlip


# Transfer object (it's basically just a pair of objects)
class transfer:
    def __init__(self, subject, mission):
        self.subject = subject
        self.mission = mission


# transferBatch object
# The batching principle works as follows:
# When transfer events (SUPPORTS and JOINS as well as their reciprocals) are processed they are simply batched up and no drawing or mission modification occurs.
# When the batch is complete, it all the lines are drawn and mission changes made in one go.
class transferBatch:
    def __init__(self, date):
        self.date = date
        self.supports = []
        self.unSupports = []
        self.joins = []
        self.leaves = []
        self.touchedMissions = []   # A list of all missions involved (touched).


    # Add a SUPPORTS event to the batch.
    def addSupports(self, craft, mission):
        if not(mission in self.touchedMissions):
            self.touchedMissions.append(mission)
        t = transfer(craft, mission)
        self.supports.append(t)

    # Add a unSUPPORTS event to the batch.
    def addUnSupports(self, craft, mission):
        if not(mission in self.touchedMissions):
            self.touchedMissions.append(mission)
        t = transfer(craft, mission)
        self.unSupports.append(t)

    # Add a JOINS event to the batch.
    def addJoins(self, traveler, mission):
        if not(mission in self.touchedMissions):
            self.touchedMissions.append(mission)
        t = transfer(traveler, mission)
        self.joins.append(t)

    # Add a leaves event to the batch.
    def addLeaves(self, traveler, mission):
        if not(mission in self.touchedMissions):
            self.touchedMissions.append(mission)
        t = transfer(traveler, mission)
        self.leaves.append(t)

    # Rearrange the slots of missions within an orbit to put the transfer batch missions into adjacent slots.
    def RV(self):
        transferOrbit = self.touchedMissions[0].orbit
        if not(transferOrbit is None):
            minSlot = 1000
            masterMissionName = None
            for m in self.touchedMissions:
                # Check that the orbit to which all of the missions are assigned matches the first one.
                if not(m.orbit is transferOrbit):
                    print("ERROR: Trying to transfer between multiple orbits! Master mission: "
                          + self.touchedMissions[0].name
                          + " is assigned to: "
                          + self.touchedMissions[0].orbit.name
                          + ". Slave mission: "
                          + self.touchedMissions[0].name
                          + " is assigned to: "
                          + self.touchedMissions[0].orbit.name)
            for m in self.touchedMissions:
                # Find which of the batch missions has the lowest index
                if m.slotIndex < minSlot:
                    minSlot = m.slotIndex
                    masterMissionName = m.name
            changedMissions = 0
            for m in self.touchedMissions:
                if m.name != masterMissionName:  # For each slave (the master does not need to be changed in any way.
                    if m.RV == 0:  # Only actually change anything if it needs to be changed.
                        changedMissions += 1  # Increment the count of missions changed.
                        transferOrbit.removeMission(m)  # Remove slave from it's current slot.
                        transferOrbit.insertMission(m, minSlot + 1)  # Insert slave mission immediately below the master.
                        m.RV = 1  # Set the RV flag.
                        minSlot += 1  # In case there are multiple RV slaves, put them into subsequent slots.
            return changedMissions  # Return the number of changed missions.

    # Execute the batch of transfers
    # First draw the impacted orbits and all the missions and lines therein
    # Then change the affected missions by making all the transfer modifications
    # Then draw all the impacted orbits again
    def execute(self, batchXPos):
        # Initialise slip.
        slip = 0
        # Check that all the missions in the TB are actually assigned to an orbit.
        # If not, execute the transfers but don't draw anything (can't work out where to draw without an orbit)
        transferOrbit = self.touchedMissions[0].orbit
        if not(transferOrbit is None):
            if logLevel > 1:
                print("INFO: Executing transfer batch at x: "
                      + str(batchXPos)
                      + " for "
                      + str(len(self.touchedMissions))
                      + " missions in orbit "
                      + transferOrbit.name)
            for m in self.touchedMissions:
                # Check that the orbit to which all of the missions are assigned matches the first one.
                if not(m.orbit is transferOrbit):
                    if logLevel > 0:
                        print("WARNING: Trying to transfer between multiple orbits! Master mission: "
                              + self.touchedMissions[0].name
                              + " is assigned to: "
                              + self.touchedMissions[0].orbit.name
                              + ". Slave mission: "
                              + m.name
                              + " is assigned to: "
                              + m.orbit.name)
            # First move the missions into RV slots.
            self.RV()
            # Draw all of the missions in this orbit after the RV.
            slip += 20
            slip += transferOrbit.draw(batchXPos + slip)
            slip += 2
            # Now draw the affected missions a second time. This is to give space to close out any bends.
            thisSlip = 0
            maxSlip = 0
            for m in self.touchedMissions:
                thisSlip = m.draw(batchXPos + slip)
                if thisSlip > maxSlip:
                    maxSlip = thisSlip
            slip += maxSlip

            # Now close the mission lines.
            for m in self.touchedMissions:
                m.closeDraw()
        else:
            if logLevel > 0:
                print("WARNING: Transfer group not drawn as master mission "
                      + self.touchedMissions[0].name
                      + " is not assigned an orbit")
        # Execute all of the batched transfer events - do the removals first or the mission attribute of the components will be set to null by the remove.
        for x in self.unSupports:
            x.mission.removeCraft(x.subject)
        for x in self.supports:
            x.mission.addCraft(x.subject)
        for x in self.leaves:
            x.mission.removeTraveler(x.subject)
        for x in self.joins:
            x.mission.addTraveler(x.subject)
        # Capture the above in a new state object (grabs lots of details about the mission)
        for m in self.touchedMissions:
            m.currentState = missionState(m, self.date)
        # Make space for the transfers so that they are not vertical lines.
        if not(transferOrbit is None):
            slip += 30
            # Draw a snapshot of all the missions in the orbit after the change.
            slip += transferOrbit.draw(batchXPos + slip)
            # Because we are starting a brand new mission line here (remeber the close above?) need a second draws to create a horizontal line
            slip += 2
            slip += transferOrbit.draw(batchXPos + slip)
        return slip


# Constructor function for lineOffset object
# - Offset of this line from the centre point of the line group.
#   Right is positive. Should always be less than half the width.
# - Reference to the line creating object (can be either a craft or traveler)
class lineOffset:
    def __init__(self, offset, lineObject):
        self.offset = offset
        self.lineObject = lineObject


# missionState object - captures the current state of the mission for drawing purposes.
# - Width
# - ID of relevant HTML details panel
# - Array of lineOffsets
# - Creator - Accepts mission as parameter
# - Draw - Draws lines from array, accepts two vector parameters, draw point and vector representing direction and scale of the group of line points.
class missionState:
    def __init__(self, missionObj, date=None):
        # Only create a detail skeleton if passed a date
        if date is None:
            self.panelId = 0
        else:
            self.sk = missionObj.createDetailSkeleton(date)
            self.panelId = self.sk.panelId
        self.width = missionObj.width()
        self.lineGroup = []
        # Iterate through all of the craft and add a record for each to the line group.
        craftOffset = 0
        for c in missionObj.craft:
            # Move in by half a width both before and after the draw. This puts the line in between middle of the width gap.
            halfCraftWidth = c.width / 2
            craftOffset += halfCraftWidth
            self.lineGroup.append(lineOffset(craftOffset, c))
            craftOffset += halfCraftWidth
        # Iterate through all of the travelers and add a record for each to the line group.
        # Define the start point by offsetting each traveler such that they are spaced out
        if len(missionObj.travelers) > 0:
            travelerGap = self.width / len(missionObj.travelers)
            # Start out at half a gap in. This will put each line in the middle of it's space.
            travelerOffset = travelerGap / 2
            for tv in missionObj.travelers:
                self.lineGroup.append(lineOffset(travelerOffset, tv))
                travelerOffset += travelerGap

    # Draw function
    # Draws new points for all the lines listed within the lineGroup property.
    # Parameter position is a vector from the origin to the intended centre point of the line points group.
    # Parameter LGV is the line group vector. It is a vector that describes the direction of the line points group and also it's scale. A unity vector (length 1) should draw the group at it's intended width.
    # TurnTest is optional. 0 means straight line, 1 means arc right, -1 means arc left.
    def draw(self, position, LGV, turnTest=0):
        # Vector from the draw point to the start of the group.
        halfOutVector = LGV * (-0.5 * self.width)
        # Vector from the origin to the start of the group
        LGStart = position + halfOutVector
        scaleFactor = vf.eDist(LGV)
        radius = 0
        for l in self.lineGroup:
            # Scale the line group vector for this point.
            pointVector = LGV * l.offset
            # Add the scaled LGV to the start point to get the absolute coords for this point.
            pointVector += LGStart
            if turnTest == -1:
                radius = l.offset * scaleFactor * -1
            if turnTest == 1:
                radius = self.width - l.offset * scaleFactor
            l.lineObject.draw(self.panelId, pointVector[0], pointVector[1], "black", radius)


# mission object
class mission:
    def __init__(self, name):
        self.name = name  # String name
        self.x = None  # The co-ords of the most recent point drawn for this mission
        self.y = None
        self.lastVector = None  # The last vector drawn for self mission. Allows subsequent draws to take account of the direction of the last draw.
        self.orbit = None  # The orbit (object) in which the mission currently resides.
        self.slotIndex = None  # Index of the orbital slot to which this mission is assigned
        self.craft = []  # List of craft assigned to the mission
        self.travelers = []  # List of space travellers assigned to this mission (i.e. people, crew and/or passengers/tourists).
        self.lastState = None  # The state the mission was in the last time it was drawn (need to remember as we've not yet drawn the bend at the end of that line)
        self.lastInset = 0  # If there is a bend at the begining of the "lastVector", how much space does it take up?
        self.RV = 0  # Rendezvous flag. 1 means this mission is currently rendezvoused with another, 0 means it's free flying.
        self.currentDetailSkeleton = None
        self.currentState = missionState(
            self)  # Create missionState to define the mission's initial state (very empty). Because the date parameter has been omitted this call will not also generate a detail panel skeleton

    # Comparison function for mission
    def __eq__(self, other):
        # Comparing with str
        if isinstance(other, str):
            return self.name == other
        # Comparing with another mision object
        elif isinstance(other, mission):
            return self.name == other.name

    # Function to add up the widths of all the constituent craft
    def width(self):
        a = 0
        for craft in self.craft:
            a = a + craft.width
        return a

    # Function to create a skeleton detail panel for later
    def createDetailSkeleton(self, date):
        sk = skeleton(self, date)
        if self.currentDetailSkeleton:
            self.currentDetailSkeleton.endDate = date  # If this isn't the first detail skeleton to be created for this mission, update the end date of the previous one.
            self.currentDetailSkeleton.sucessor = sk
            sk.predecessor = self.currentDetailSkeleton
        self.currentDetailSkeleton = sk
        return sk

    # Function to add a craft to this mission
    def addCraft(self, newCraft):
        newCraft.mission = self.name
        self.craft.append(newCraft)

    # Function to remove a craft from this mission
    def removeCraft(self, exCraft):
        exCraft.mission = None
        if exCraft in self.craft:
            self.craft.remove(exCraft)
        else:
            print("ERROR: Removing craft " + exCraft.name + " from mission " + self.name + ". Could not find craft.")

    # Function to add a traveler to this mission
    def addTraveler(self, newTraveler):
        newTraveler.mission = self.name
        self.travelers.append(newTraveler)

    # Function to remove a traveler from this mission
    def removeTraveler(self, exTraveler):
        exTraveler.mission = None
        if exTraveler in self.travelers:
            self.travelers.remove(exTraveler)
        else:
            print("ERROR: Removing traveler "
                  + exTraveler.name
                  + " from mission "
                  + self.name
                  + ". Could not find traveler.")

    # Mission Draw Function
    # Features a number of different draw styles for bends.
    # Accepts x and y coords for the new mission point.
    # bendstyle parameter defaults to "ARC". Other option is "MITRE". Arcs look prettier but are a LOT more complicated to draw.
    # Note that this method is VERY stateful as the bends need to know where the mission is going next.
    # States:
    # Unitialised:
    #   The mission has never been drawn before. Its x and y properties are set to None.
    #   The draw method simply initialises the mission by setting the x and y properties to the values passed into it.
    # Initialised as point:
    #   The mission has been drawn ONCE before. It has x and y properties but no last vector.
    #   The draw method creates a lastVector object as a property, this is a vector from the previous draw point to this one.
    # Initialised with vector:
    #   The mission has been drawn TWICE before. It has a lastVector property.
    #   The draw method actually draws the previous section of lines (so not to the point passed in this time, but last time).
    #   This is because the bend take up space so it's not possible to draw a line without knowing where the next section. is going.

    def draw(self, newX, newY=None, bendstyle="ARC"):
        # If a new y-axis value isn't supplied keep y-axis value the same as before (note that this could well be "None")
        if newY is None:
            newY = self.y

        # Initialise slip
        slip = 0

        # Check that both the x and y values were set last time.
        # This function draws a line from somewhere to somewhere else. It cannot start from nowhere.
        if self.x is None or self.y is None:
            # It's important to remember the new position as it will be the previous one next time.
            self.x = newX
            self.y = newY
            self.lastState = self.currentState  # Same goes for state.
            if logLevel > 1:
                print("INFO: Mission: "
                      + self.name
                      + " initialised at "
                      + str(self.x)
                      + "," + str(self.y)
                      + " (previously null)")
            return 0

        # Check that the new draw point is further down the x-axis than last time. The graph must always progress left to right.
        if self.x > newX:
            diff = self.x - newX
            slip += diff
            if logLevel > 0:
                print("WARNING: Mission: "
                      + self.name
                      + " slipped by "
                      + str(diff)
                      + " as new draw point "
                      + str(newX)
                      + " is to the left of previous ("
                      + str(self.x)
                      + ")")

        # Check that the new draw point is not the same as the previous one. As well as saving compute, it's actually impossible to calculate a vector at right angle to one with no magnitude and a div/0 ensues...
        if (self.x == newX + slip) and (self.y == newY):
            self.lastState = self.currentState  # Still update the state
            if logLevel > 0:
                print("WARNING: Mission: "
                      + self.name
                      + " not drawn as same position: "
                      + str(self.x)
                      + ","
                      + str(self.y))
            return 0

        # Bend resolution
        # When drawing a mission group of lines bends between lines cannot be drawn until the next line is added.
        # This function is therefore always one draw behind.
        # There are several cases:
        # - No previous vector: Add a group of line points at right angles to the current (invisible) vector at it's start.
        #   This will be extended next time.
        # - Previous vector acute to current: draw a simple bend.
        # - Previous vector obtuse to current: add an extra line section to accommodate an extra large bend.
        # Create a vector for the mission line we're currently drawing
        currentVector = np.array([newX + slip - self.x, newY - self.y])
        # Unity version of the current mission line vector
        currentUnityVector = vf.unity(currentVector)
        # Define the start point of the current mission line
        lineGroupCentre = np.array([self.x, self.y])

        # No previous vector case. I.e. the start of a mission line.
        if self.lastVector is None:
            if self.lastState is None:
                print("ERROR: Mission "
                      + self.name
                      + " lineGroup cannot be drawn (first vector) at "
                      + str(self.x) + "," + str(self.y)
                      + " as lastState is not defined. New point: "
                      + str(newX) + "," + str(newY))
                return 0
            # Define line group vector, this is perpendicular to the mission line
            lineGroupVector = vf.rotCW270(currentUnityVector)
            # Draw the all of the lines using this new line group vector
            self.lastState.draw(lineGroupCentre, lineGroupVector)
            self.x = newX + slip
            self.y = newY
            self.lastState = self.currentState
            self.lastVector = currentVector
            if logLevel > 1:
                print("INFO: Mission: "
                      + self.name
                      + " draw to: "
                      + str(self.x) + "," + str(self.y)
                      + " (first vector)")
            return 0

        # Cases with a previous vector
        if not(self.lastVector is None):
            lastUnityVector = vf.unity(self.lastVector)
            # Define the tangent vector: adding the unity versions of the two vectors gives a vector which is tangential to the bend.
            tangentVector = lastUnityVector + currentUnityVector

            # Check for 0 angle, i.e. a draw is an extension of the previous in exactly the same direction.
            # If this is the case it is only necessary to perform a draw if the state has changed.
            # A tangent vector length of 2 can only mean that the last unity vector and the current unity vector are identical in direction.
            if vf.eDist(tangentVector) == 2:
                # Check if the state hasn't changed
                if self.lastState is self.currentState:
                    self.x = newX + slip
                    self.y = newY
                    # Add the current vector to the last vector, this will just make the last vector longer, which might be important later on
                    self.lastVector += currentVector
                    if logLevel > 1:
                        print("INFO: Mission " + self.name + " is extension of previous draw to " + str(
                            self.x) + "," + str(self.y))
                    return 0

            # Mitre joint, like when joining skirting boards, or cornice etc.
            # Can handle angles greater than 90deg but it's a bit rubbish.
            if bendstyle == "MITRE":
                # Slightly lost track of why this works, but it does somehow scale the tangent vector to the correct length.
                lineGroupVector = tangentVector * (2 / np.sum(tangentVector **2))
                lineGroupVector = vf.rotCW270(lineGroupVector)  # Because our coordinates system has +y down, this is actually a CW90 turn.
                # The line group vector is now the mitre joint.
                self.lastState.draw(lineGroupCentre, lineGroupVector)
            # Arc bends, uses arcs to create curved bends.
            # Handles all cases inc acute, obtuse and 0 and 180 deg bends.
            elif bendstyle == "ARC":
                # Check for special case of double back, this is when the bend needs to be 180 degrees which is impossible for the normal bend algorithm.
                doubleBack = 0
                if vf.eDist(tangentVector) == 0:
                    # Need to offset the two line groups to the side of the vectors rather than along them. bendOffsetVector captures this translation.
                    bendOffsetVector = np.copy(lastUnityVector)
                    bendOffsetVector *= (self.lastState.width + 2)  # Little gap between the two should make it clearer.
                    bendOffsetVector = vf.rotCW270(bendOffsetVector)
                    doubleBack = 1
                    if bendOffsetVector[0] < 0:  # Choose which way to go, try to go towards x positive.
                        bendOffsetVector = vf.rotCW180(bendOffsetVector)
                        doubleBack = -1
                    lineGroupCentre1 = np.copy(lineGroupCentre)
                    lineGroupCentre2 = lineGroupCentre1 + bendOffsetVector
                    slip += bendOffsetVector[0]
                    newY += bendOffsetVector[1]  # Need to slip in y as well.
                    if logLevel > 1:
                        print("INFO: Mission "
                              + self.name
                              + " slipped due to doubleback, vector: "
                              + bendOffsetVector[0]
                              + ","
                              + bendOffsetVector[1])
                    inset = self.lastState.width / 2  # 180 degree bend but treated like two 90s.
                    lineGroupCentre1 += lastUnityVector * (-1 * inset)  # Step back down the incoming vector
                    lineGroupCentre2 += currentUnityVector * (1 * inset)  # Step forward along the current vector
                else:
                    bendOffsetVector = np.array([0.0, 0.0])
                    # Calculate a vector at right angle to the bend by subtracting the direction of one vector for the other.
                    normalVector = currentUnityVector - lastUnityVector
                    # It turns out that the ratio of the lengths of these two is equal to the ratio between half the width and the inset.
                    inset = (self.lastState.width / 2) * (vf.eDist(normalVector) / vf.eDist(tangentVector))
                    if inset > self.lastState.width / 2:  # Obtuse bend case
                        insetExcess = inset - self.lastState.width / 2
                        inset = self.lastState.width / 2
                        bendOffsetVector += lastUnityVector * insetExcess
                        bendOffsetVector += currentUnityVector * insetExcess
                        slip += bendOffsetVector[0]
                        newY += bendOffsetVector[1]
                        if logLevel > 1:
                            print(
                                "INFO: Mission " + self.name + " slipped due to obtuse bend. Vector: " + bendOffsetVector[0] + "," + bendOffsetVector[1])
                    if (inset + self.lastInset) > vf.eDist(self.lastVector):
                        # There isn't room for both bends on the last line segment
                        diff = inset + self.lastInset - vf.eDist(self.lastVector)
                        lastSlipVector = lastUnityVector * diff
                        slip += lastSlipVector[0]
                        newY += lastSlipVector[1]
                        lineGroupCentre += lastSlipVector
                        if logLevel > 1:
                            print(
                                "INFO: Mission "
                                + self.name
                                + " slipped as last segment is shorter than it's two bends. Vector: "
                                + str(lastSlipVector[0])
                                + ","
                                + str(lastSlipVector[1]))
                    # Step back down the incoming vector
                    lineGroupCentre1 = lineGroupCentre + lastUnityVector * (-1 * inset)
                    # Step forward along the current vector
                    lineGroupCentre2 = lineGroupCentre + currentUnityVector * (1 * inset)
                    lineGroupCentre2 += bendOffsetVector
                lastUnityVector = vf.rotCW270(lastUnityVector)  # The line group vectors are just simple rotations of the unity vectors
                # Need to work out whether angle between two vectors is positive or negative. Scalar P is prop to Cosine. Cos of angle rotated by 90deg is Sine.
                turnTest = np.dot(lastUnityVector, currentUnityVector)
                currentUnityVector = vf.rotCW270(currentUnityVector)
                if turnTest > 0 or doubleBack > 0:
                    turnTest2 = 1
                if turnTest < 0 or doubleBack < 0:
                    turnTest2 = -1
                if turnTest == 0 and doubleBack == 0:
                    turnTest2 = 0
                self.lastState.draw(lineGroupCentre1, lastUnityVector)  # First line (up to bend) is straight.
                if inset > 0:  # Only draw bend if there is actually a bend to draw
                    self.lastState.draw(lineGroupCentre2, currentUnityVector, turnTest2)  # Second line is an arc.
                # Check to see if the bend takes up more space than is available
                if inset > vf.eDist(currentVector):
                    diff = inset - vf.eDist(currentVector)
                    # Rotate the vector back (were previously using it as the direction of the line group which is perpendicular)
                    currentUnityVector = vf.rotCW90(currentUnityVector)
                    slipVector = currentUnityVector * diff
                    slip += slipVector[0]
                    newY += slipVector[1]
                    if logLevel > 1:
                        print(
                            "INFO: Mission "
                            + self.name
                            + " slipped as bend is larger than draw, vector: "
                            + str(slipVector[0])
                            + ","
                            + str(slipVector[1]))
                self.lastInset = inset

            self.x = newX + slip
            self.y = newY
            self.lastState = self.currentState
            self.lastVector = currentVector
            if logLevel > 1:
                print(
                    "INFO: Mission: "
                    + self.name
                    + " draw to: "
                    + str(self.x)
                    + ","
                    + str(self.y)
                    + " (slipped "
                    + str(slip)
                    + ")")
            return slip

    # Closes mission line by drawing a final end cap.
    def closeDraw(self):
        # Need to know where we are and which direction we're pointing in.
        if not(self.x is None) and not(self.y is None) and not(self.lastVector is None):
            lineGroupCentre = np.array([self.x, self.y])  # Defines the start point of the current mission line.
            lastUnityVector = self.lastVector * (1 / vf.eDist(self.lastVector))
            lastUnityVector = vf.rotCW270(lastUnityVector)  # The line group vectors are just simple rotations of the unity vectors
            self.lastState.draw(lineGroupCentre, lastUnityVector)
            if logLevel > 1:
                print("INFO: Mission: "
                      + str(self.name)
                      + " closing draw draw at "
                      + str(self.x)
                      + ","
                      + str(self.y))
        else:
            if logLevel > 0:
                print("WARNING: Mission: "
                      + str(self.name)
                      + " unable to close draw at "
                      + str(self.x)
                      + ","
                      + str(self.y)
                      + " as either present position on last vector are not defined.")
        self.lastState = self.currentState  # Move state
        # If any more drawing is to be done for this mission it cannot carry on from this point but must start anew.
        self.x = None
        self.y = None
        self.lastVector = None
        self.lastState = None
        self.lastInset = 0

    # Destructor function
    # Removes all craft and travelers from mission. Removes mission from orbit. Removes mission from various lists.
    def end(self, date):
        # Finish off hanging bends.
        self.closeDraw()
        # Define the end date of the final skeleton
        self.currentDetailSkeleton.endDate = date
        # Reset all travelers and craft. This resets them to the state they were in when first created. This will prevent their lines being drawn between missions.
        for t in self.travelers:
            t.x = None
            t.y = None
        for c in self.craft:
            c.x = None
            c.y = None
        # Remove references from traveler objects
        while len(self.travelers) > 0:
            toBeRemoved = self.travelers.pop()
            toBeRemoved.mission = None
        # Remove references from craft objects
        while len(self.craft) > 0:
            toBeRemoved = self.craft.pop()
            toBeRemoved.mission = None
        # Remove mission from orbit (thus freeing up the slot for another mission)
        if not(self.orbit is None):
            try:
                self.orbit.removeMission(self)
            except ValueError:
                print("Mission " + self.name + ": Orbit " + self.orbit.name + " is not defined.")
        self.orbit = None


# Mission panel skeleton
class skeleton:
    skeletonList = []

    def __init__(self, currentMission, date):
        self.doc = minidom.Document()
        if date:
            self.startDate = date
        else:
            self.startDate = None
        self.endDate = None
        self.sucessor = None
        self.predecessor = None
        self.written = 0  # Flag to indicate whether or not a skeleton has been written into the document
        self.panelId = random.randint(0, 4294967295)  # Create a random 32bit integer.
        self.name = currentMission.name
        self.travelers = []
        for t in currentMission.travelers:
            self.travelers.append(t.name)
        self.craft = []
        for c in currentMission.craft:
            self.craft.append(c.name)
        skeleton.skeletonList.append(self)

    def toXml(self):
        skRoot = self.doc.createElement("ms")
        skRoot.setAttribute("pId", str(self.panelId))
        skRoot.setAttribute("name", self.name)
        if self.startDate:
            skRoot.setAttribute("sDate", self.startDate.isoformat())
        if self.endDate:
            skRoot.setAttribute("eDate", self.endDate.isoformat())
        if self.predecessor:
            skRoot.setAttribute("pre", str(self.predecessor.panelId))
        if self.sucessor:
            skRoot.setAttribute("suc", str(self.sucessor.panelId))

        for c in self.craft:
            el = self.doc.createElement("cr")
            tn = self.doc.createTextNode(c)
            el.appendChild(tn)
            skRoot.appendChild(el)
        for t in self.travelers:
            el = self.doc.createElement("tv")
            tn = self.doc.createTextNode(t)
            el.appendChild(tn)
            skRoot.appendChild(el)
        return skRoot


# Component - common things between craft and traveler
class component:
    def __init__(self, name, SVGLayer):
        self.doc = minidom.Document()
        self.name = name  # String name
        self.mission = None  # Mission to which the component is currently assigned
        self.x = None  # The co-ords of the most recent point drawn
        self.y = None
        self.drawFlag = 0  # Used to record whether or not draw function has ever been called on this craft
        self.lastPanel = None
        self.currentPath = None
        self.lineGroupElement = self.doc.createElementNS("http://www.w3.org/2000/svg", "g")
        self.lineGroupElement.setAttribute("class", self.groupClass)
        self.lineGroupElement.setAttribute("id", self.name)
        self.lineGroupElement.setAttribute("style", self.groupStyle)
        SVGLayer.appendChild(self.lineGroupElement)

    # Comparison function for components
    def __eq__(self, other):
        # Comparing with str
        if isinstance(other, str):
            return self.name == other
        # Comparing with another component object
        elif isinstance(other, component):
            return self.name == other.name

    # Draws a line from the previous point to a new one. Common to both craft and traveler;
    def draw(self, missionPanelId, newX, newY, colour, radius):
        self.drawFlag = 1
        # If the line is to the same coords as the previous draw to nothing.
        if not (self.x == newX and self.y == newY):
            # If the mission panel id has changed create a new line
            if self.lastPanel != missionPanelId:
                self.currentPath = self.doc.createElementNS("http://www.w3.org/2000/svg", "path")
                self.currentPath.setAttribute("missiondetailpanel", str(missionPanelId))
                self.lineGroupElement.appendChild(self.currentPath)
                # If either the current x or y values are null start the path using the newX and newY.
                if self.x is None and self.y is None:
                    d = "M " + str(round(newX, 1)) + " " + str(round(newY, 1)) + " "
                    if logLevel > 1:
                        print("INFO: Initialising line " + self.name + " at " + str(newX) + "," + str(newY))
                    self.currentPath.setAttribute("d", d)
                    self.x = newX
                    self.y = newY
                    self.lastPanel = missionPanelId
                    return
                # Otherwise start the path using the previous x and y
                else:
                    d = "M " + str(round(self.x, 1)) + " " + str(round(self.y, 1)) + " "
                    self.currentPath.setAttribute("d", d)
            # Append this draw to the existing path (possibly including the one we just created)
            if radius:  # If a radius is specified draw an arc
                direction = 1
                if radius < 0:  # The direction of the radius indicates the direction of the arc, CW or CCW
                    radius = radius * -1  # Radius must be positive
                    direction = 0  # 1 = CCW
                d = self.currentPath.getAttribute("d")
                d += "A" + str(round(radius, 1)) + " " + str(round(radius, 1)) + " 0 0 " + str(direction) + " " + str(
                    round(newX, 1)) + " " + str(round(newY, 1)) + " "
                self.currentPath.setAttribute("d", d)
                if logLevel > 1:
                    print("INFO: Line " + self.name + " drawn arc to " + str(newX) + "," + str(newY))
            else:
                d = self.currentPath.getAttribute("d")
                d += "L " + str(round(newX, 1)) + " " + str(round(newY, 1)) + " "
                self.currentPath.setAttribute("d", d)
                if logLevel > 1:
                    print("INFO: Line " + self.name + " drawn straight to " + str(newX) + "," + str(newY))
            self.lastPanel = missionPanelId
            self.x = newX
            self.y = newY
        else:
            if logLevel > 0:
                print("WARNING: Line " + self.name + " not drawn due to zero length")


# craft object
class craft(component):
    def __init__(self, name, SVGLayer, width=14, hue=random.randint(0, 360)):
        self.width = width
        self.hue = hue
        self.cssClass = "craft"
        self.groupClass = "craftGroup"
        self.groupStyle = "stroke:hsl(" + str(self.hue) + ",50%,50%);stroke-width:" + str(self.width) + ";"
        component.__init__(self, name, SVGLayer)

    def styleString(self):
        return "stroke:hsl(" + str(self.hue) + ",50%,50%);stroke-width:" + str(self.width) + ";"


# traveler object
class traveler(component):
    def __init__(self, name, SVGLayer):
        self.cssClass = "traveler"
        self.groupClass = "travelerGroup"
        self.groupStyle = ""
        component.__init__(self, name, SVGLayer)

    def styleString(self):
        return ""
