from datetime import datetime
from xml.dom import minidom
import spaceflight as sf

logLevel = 0
sf.logLevel = 0


# SpaceEvent class
class SpaceEvent:
    def __init__(self, xmlevent):
        for f in xmlevent.childNodes:
            if f.nodeType == 1:
                if f.localName == 'date':
                    self.date = datetime.fromisoformat(f.firstChild.data)
                elif f.localName == 'subject':
                    self.subject = f.firstChild.data
                elif f.localName == 'eventType':
                    self.eventType = f.firstChild.data
                elif f.localName == 'object':
                    self.object = f.firstChild.data

    def print(self):
        print('Date: ' + self.date.strftime("%d/%m/%Y"))
        print('Subject: ' + self.subject)
        print('Event Type: ' + self.eventType)
        if self.eventType != 'ENDS':
            print('Object: ' + self.object)


# MAIN Routine
epochDate = datetime.fromisoformat("1970-01-01T00:00:00.000")
secPerDay = 24 * 60 * 60
# The number of pixels per day.
dayWidth = 10
# Ratio between the time difference in seconds and the draw grid. This value should give 20px per day.
xRatio = secPerDay / dayWidth
# A stretching of the x-axis in pixels to accomodate things that don't fit
timeSlip = 0


def drawdate(date):
    timeD = date - startDate
    secsFromStart = timeD.total_seconds()
    xPosition = secsFromStart / xRatio + timeSlip
    textElement = outDoc.createElementNS("http://www.w3.org/2000/svg", "text")
    textElement.setAttribute("x", str(round(xPosition - 5)))
    textElement.setAttribute("y", "520")
    textElement.setAttribute("transform", "rotate(90," + str(round(xPosition - 5)) + " , 520)")
    textElement.setAttribute("id", date.isoformat())
    tn = outDoc.createTextNode(date.strftime("%d/%m/%Y"))
    textElement.appendChild(tn)
    gridLinesLayer.appendChild(textElement)


# Parse xml event list into a list of python spaceEvent objects + startDate global
mydoc = minidom.parse('Data/eventList.xml')
xmlSpaceEventList = mydoc.getElementsByTagName('spaceEvent')
spaceEventList = []
for xmlSpaceEvent in xmlSpaceEventList:
    thisSpaceEvent = SpaceEvent(xmlSpaceEvent)
    spaceEventList.append(thisSpaceEvent)
startDate = spaceEventList[0].date

# Define the structure of the XML document to which we will be writing
outDoc = minidom.Document()

htmlE = outDoc.createElement("html")
outDoc.appendChild(htmlE)

headE = outDoc.createElement("head")
headE.innerHTML = '<link rel="stylesheet" type="text/css" href="timeline.css">'
htmlE.appendChild(headE)

scriptE = outDoc.createElement("script")
scriptE.setAttribute("src", "timeline.js")
t = outDoc.createTextNode("")
scriptE.appendChild(t)
headE.appendChild(scriptE)

codeE = outDoc.createElement("code")
codeE.setAttribute("style", "display:none;")
skCollectionRoot = outDoc.createElement("missionStates")
codeE.appendChild(skCollectionRoot)
headE.appendChild(codeE)

linkE = outDoc.createElement("link")
linkE.setAttribute("rel", "stylesheet")
linkE.setAttribute("type", "text/css")
linkE.setAttribute("href", "timeline.css")
headE.appendChild(linkE)

bodyE = outDoc.createElement("body")
bodyE.setAttribute("onload", "completeDraw();")
htmlE.appendChild(bodyE)

svgDivE = outDoc.createElement("div")
svgDivE.setAttribute("height", "600")
svgDivE.setAttribute("style", "overflow:auto; border:1px solid black;")
bodyE.appendChild(svgDivE)

SVGElement = outDoc.createElementNS("http://www.w3.org/2000/svg", "SVG")
SVGElement.setAttribute("xmlns", "http://www.w3.org/2000/svg")
SVGElement.setAttribute("width", "1024")
SVGElement.setAttribute("height", "600")
svgDivE.appendChild(SVGElement)

backgroundLayer = outDoc.createElement("g")
SVGElement.appendChild(backgroundLayer)

gridLinesLayer = outDoc.createElement("g")
gridLinesLayer.setAttribute("id", "gridLinesLayer")
SVGElement.appendChild(gridLinesLayer)

craftLayer = outDoc.createElement("g")
craftLayer.setAttribute("id", "craftLayer")
SVGElement.appendChild(craftLayer)

travelerLayer = outDoc.createElement("g")
travelerLayer.setAttribute("id", "travelerLayer")
SVGElement.appendChild(travelerLayer)

detailDiv = outDoc.createElement("div")
detailDiv.setAttribute("id", "detailArea")
detailDiv.setAttribute("style", "border:1px solid black;")
bodyE.appendChild(detailDiv)

lineDetailDiv = outDoc.createElement("div")
lineDetailDiv.setAttribute("id", "lineDetailArea")
lineDetailDiv.setAttribute("style", "height:30px;")
t = outDoc.createTextNode("")
lineDetailDiv.appendChild(t)
detailDiv.appendChild(lineDetailDiv)

missionDetailDiv = outDoc.createElement("div")
missionDetailDiv.setAttribute("id", "missionDetailArea")
detailDiv.appendChild(missionDetailDiv)

# Initialise variables for event processing
craftList = []
travelerList = []
missionList = []
lastGridLineTime = startDate
activeTransferBatch = None
orbitList = [
    sf.orbit("Heliocentric", 0, 15, "rgb(255,255,192)"),
    sf.orbit("Lunar_Surface", 15, 15, "rgb(128,128,128)"),
    sf.orbit("Lunar_Orbit", 30, 45, "rgb(192,192,192)"),
    sf.orbit("Lunar_Flyby", 75, 20, "rgb(224,224,224)"),
    sf.orbit("HEO", 95, 20, "rgb(224,224,255)"),
    sf.orbit("LEO", 115, 350, "rgb(192,192,255)"),
    sf.orbit("Sub_Orbital", 465, 20, "rgb(160,160,255)"),
    sf.orbit("Earth", 485, 35, "rgb(160,255,160)")]

# Parse xml craft list into a list of python craft objects
mydoc = minidom.parse('Data/craftList.xml')
xmlCraftList = mydoc.getElementsByTagName('craft')
for xmlCraft in xmlCraftList:
    for field in xmlCraft.childNodes:
        if field.nodeType == 1:
            if field.localName == 'name':
                xmlCraftName = field.firstChild.data
            elif field.localName == 'CrewCapacity':
                xmlCraftWidth = int(field.firstChild.data) * 7
            elif field.localName == 'Hue':
                xmlCraftHue = int(field.firstChild.data)
    newCraft = sf.craft(xmlCraftName, craftLayer, xmlCraftWidth, xmlCraftHue)
    craftList.append(newCraft)

for spaceEvent in spaceEventList:
    # Update the X position at which we're writing using the date of the event.
    eventDate = spaceEvent.date
    # epochDiff = eventDate - epochDate
    # epochDiffSeconds = epochDiff.total_seconds()

    # Various conditions under which an active transfer batch should be executed and deleted.
    # - Date has moved on.
    # - Event type is not either SUPPORTS or JOINS
    if not(activeTransferBatch is None):
        if activeTransferBatch.date != eventDate or not (
                spaceEvent.eventType == "SUPPORTS" or spaceEvent.eventType == "JOINS"):
            # Use the batch's date to work out where on the x-axis to draw the batched events. Note that transfer events don't change the y-axis value of missions, only their components.
            timeDiff = activeTransferBatch.date - startDate
            secondsFromStart = timeDiff.total_seconds()
            executionXPos = secondsFromStart / xRatio + timeSlip
            timeSlip += activeTransferBatch.execute(executionXPos)
            activeTransferBatch = None

    # If a grid line has not yet been drawn for this time point,
    # draw one, and also fill in all those since the last time point.
    if lastGridLineTime != eventDate:
        drawdate(eventDate)
        lastGridLineTime = eventDate

    if spaceEvent.eventType == "SUPPORTS":
        # Check to see if a transfer batch is active, if not, create a new one.
        if activeTransferBatch is None:
            activeTransferBatch = sf.transferBatch(eventDate)
        # Find the craft object, or create a new one and add it to the list
        try:
            ci = craftList.index(spaceEvent.subject)  # Find the craft with the correct name from craft list
            subjectCraft = craftList[ci]
        except ValueError:  # IF there isn't one, create one.
            subjectCraft = sf.craft(spaceEvent.subject, craftLayer)
            craftList.append(subjectCraft)
            if logLevel > 0:
                print("WARNING: Craft missing from imported craft list: " + subjectCraft.name)
        # Find the mission object to which the event refers
        try:
            mi = missionList.index(spaceEvent.object)  # Find the mission with the correct name from mission list
            objectMission = missionList[mi]
        except ValueError:  # IF there isn't one, create one.
            objectMission = sf.mission(spaceEvent.object)
            missionList.append(objectMission)
        # Add a supports entry to the transfer batch
        activeTransferBatch.addSupports(subjectCraft, objectMission)
        # If the craft is already assigned to a mission, find it and use it to create an unSupport entry.
        if not(subjectCraft.mission is None):
            try:
                mi = missionList.index(subjectCraft.mission)  # Find the mission with the correct name from mission list
            except ValueError:
                print("ERROR: Craft "
                      + subjectCraft.name
                      + " is assigned to a mission "
                      + subjectCraft.mission
                      + " that cannot be found in master mission list")
            else:
                activeTransferBatch.addUnSupports(subjectCraft, missionList[mi])

    elif spaceEvent.eventType == "JOINS":
        # Check to see if a transfer batch is active, if not, create a new one.
        if activeTransferBatch is None:
            activeTransferBatch = sf.transferBatch(eventDate)
        # Find the traveler object, or create a new one and add it to the list
        try:
            ci = travelerList.index(spaceEvent.subject)  # Find the traveler with the correct name from traveler list
            subjectTraveler = travelerList[ci]
        except ValueError:  # IF there isn't one, create one.
            subjectTraveler = sf.traveler(spaceEvent.subject, travelerLayer)
            travelerList.append(subjectTraveler)
        # Find the mission object to which the event refers
        try:
            mi = missionList.index(spaceEvent.object)  # Find the mission with the correct name from mission list
            objectMission = missionList[mi]
        except ValueError:  # IF there isn't one, create one.
            objectMission = sf.mission(spaceEvent.object)
            missionList.append(objectMission)
        # Add a joins entry to the transfer batch
        activeTransferBatch.addJoins(subjectTraveler, objectMission)
        # If the traveler is already assigned to a mission, find it and use it to create a leaves entry.
        if not(subjectTraveler.mission is None):
            try:
                mi = missionList.index(
                    subjectTraveler.mission)  # Find the mission with the correct name from mission list
            except ValueError:
                print("ERROR: Traveler "
                      + subjectTraveler.name
                      + " is assigned to a mission "
                      + subjectTraveler.mission
                      + " that cannot be found in master mission list")
            else:
                activeTransferBatch.addLeaves(subjectTraveler, missionList[mi])

    elif spaceEvent.eventType == "ARRIVES" or spaceEvent.eventType == "DEPARTS":
        # Executing a transfer batch will right shift following events as it takes up space,
        # the timeSlip variable catches this, include it when calculating the x-axis position of these events.
        timeDiff = eventDate - startDate
        secondsFromStart = timeDiff.total_seconds()
        xPos = secondsFromStart / xRatio + timeSlip

        # Find the mission object to which the event refers
        try:
            mi = missionList.index(spaceEvent.subject)  # Find the mission with the correct name from mission list
            subjectMission = missionList[mi]
        except ValueError:  # IF there isn't one, create one.
            subjectMission = sf.mission(spaceEvent.subject)
            missionList.append(subjectMission)

        # Find the orbit
        try:
            oi = orbitList.index(spaceEvent.object)
            orbit = orbitList[oi]
        except ValueError:
            print("ERROR: Mission " + spaceEvent.subject + ": Orbit " + spaceEvent.object + " is not defined.")
            orbit = None

        if not(orbit is None) and spaceEvent.eventType == "ARRIVES":
            if logLevel > 1:
                print(
                    "INFO: Mission "
                    + spaceEvent.subject
                    + " arrives at orbit "
                    + spaceEvent.object
                    + " at x position "
                    + str(xPos))
            orbit.addMission(subjectMission)
            # Draw a mission line group on the SVG for all the missions in the orbit.
            timeSlip += orbit.draw(xPos)
            # Special extra bit for arriving back on Earth, ends mission without an explicit END.
            if spaceEvent.object == "Earth":
                subjectMission.end(eventDate)
                # Remove mission from global mission list, this will speed up future searches of this list.
                try:
                    missionList.remove(subjectMission.name)
                except ValueError:
                    print("Failed to remove mission " + subjectMission.name + " from global mission list")

        elif not(orbit is None) and spaceEvent.eventType == "DEPARTS":
            if logLevel > 1:
                print("INFO: Mission "
                      + spaceEvent.subject
                      + " departs orbit "
                      + spaceEvent.object
                      + " at x position "
                      + str(xPos))
            # Special case for Earth, all missions start here without an explicit ARRIVES.
            if spaceEvent.object == "Earth":
                orbit.addMission(subjectMission)
            # Draw a mission line group on the SVG for all the missions in the orbit,
            # note that for DEPARTS is is before the change is actually made.
            timeSlip += orbit.draw(xPos)
            orbit.removeMission(subjectMission)

    elif spaceEvent.eventType == "ENDS":
        # Find the mission object to which the event refers
        try:
            # Find the mission with the correct name from mission list
            mi = missionList.index(spaceEvent.subject)
            subjectMission = missionList[mi]
            if logLevel > 1:
                print("INFO: Mission: " + subjectMission.name + " ends.")
            subjectMission.end(eventDate)
            # Remove mission from global mission list, this will speed up future searches of this list.
            try:
                missionList.remove(subjectMission.name)
            except ValueError:
                print("Failed to remove mission " + subjectMission.name + " from global mission list")

        except ValueError:
            if logLevel > 0:
                print("WARNING: Unable to end mission " + spaceEvent.subject + " as it does not exist right now")

# Check that all the craft in our list have been drawn
for c in craftList:
    if c.drawFlag == 0:
        if logLevel > 0:
            print("WARNING: Craft " + c.name + " created but never drawn")

# Resize the svg element to accomodate everything that's been drawn
SVGElement.setAttribute("width", str(xPos + dayWidth * 2))

# Draw the orbit backgrounds (same width as SVG)
for orbit in orbitList:
    orbit.drawOrbitRectangle(backgroundLayer, 0, xPos + dayWidth * 2)

# Dump the detail panels to XML
skCollectionRoot = outDoc.createElement("missionStates")
codeE.appendChild(skCollectionRoot)
for s in sf.skeleton.skeletonList:
    skXML = s.toXml()
    skCollectionRoot.appendChild(skXML)

# Write out xml
outFile = open("Output/SpaceFlightTimeLine.html", "w")
# Write out. First string is indent of root, 2nd is indent of each sub-node, third is newline.
outDoc.writexml(outFile, "", "    ", "\n")
outFile.close()

# List out what's remaining in memory at the end (this is just a quick little visual check)
print("Missions remaining in memory at the end:")
for o in orbitList:
    print("Orbit: " + o.name)
    for m in o.slots:
        print("\tMission: " + m.name)
