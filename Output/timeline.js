// Globals
var skeletonList = [];

// Callback functions for array methods
// Callback function to compare an object using its "mission" attribute
function comparePanelId(obj){
	return obj.panelId == this;
}

// EVENT HANDLERS
function clearStyle(){
	this.style = null;
}
// Function to show/hide detail panels when the user clicks on a line
function showMissionDetail(){
	var panelId = this.getAttribute("missiondetailpanel");
	var missionPanel = document.getElementById(panelId);						// Try to find a pre-existing panel in the document
	if(!missionPanel){										// If it's not there create it
		var i = skeletonList.findIndex(comparePanelId, panelId);		// Find the relevant skeleton object
		var currentSkeleton = skeletonList[i];
		var totalSkeletons = skeletonList.length;
		// It looks nice if the detail panels are written into the document in the same order they are in the skeletonList. So, find out if any skeletons further down the list have been written out already.
		while(i < totalSkeletons && skeletonList[i].written == 0){
			i++;			
		}
		var successorPanel = null;
		// If a successor panel has already been written, grab it.
		if(i < totalSkeletons){
			successorPanel = document.getElementById(skeletonList[i].panelId);
		}
		missionPanel = currentSkeleton.createDetailPanel();
		// Add in the new panel before the successor. If there isn't one, this will write to the end (i.e. same as appendChild)
		missionDetailArea.insertBefore(missionPanel, successorPanel);
		currentSkeleton.written = 1;
	}
	else{
		// missionPanel.classList.add("flashBorderRed");
		missionPanel.addEventListener("webkitAnimationEnd", clearStyle);
		missionPanel.style.animationDuration = "2s";
		missionPanel.style.animationName = "redBorder";
	}
	missionPanel.style.display = "block";
}
function showLineOnly(){
	lineDetailArea.innerHTML = this.parentNode.getAttribute("id");
}
function hideLineOnly(){
	lineDetailArea.innerHTML = "";
}
// Function to hide the parent of this thing that called it (used to hide block containing a button)
function hideParent(){
	this.parentNode.style.display = "none";
}

// Function to highlight space travelers in the diagram (changed the class of the group to which all the lines belong)
function highlightTraveler(){
	var travelerId = this.getAttribute("travelerId");
	var travelerGroup = document.getElementById(travelerId);
	if(travelerGroup){
		travelerGroup.setAttribute("class", "travelerGroupHighlight");
	}
}
function unHighlightTraveler(){
	var travelerId = this.getAttribute("travelerId");
	var travelerGroup = document.getElementById(travelerId);
	if(travelerGroup){
		travelerGroup.setAttribute("class", "travelerGroup");
	}
}

function drawDateLine(xPosition, SVGlayer){
	const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
	line.setAttribute("x1", xPosition);
	line.setAttribute("y1", 0);
	line.setAttribute("x2", xPosition);
	line.setAttribute("y2", 520);
	line.setAttribute("class", "dateLine");
	SVGlayer.appendChild(line);
}

// Function to create a detail panel to capture the current state of the mission
function createMissionDetailPanelFromSkeleton(){		
	var i;
	var htmlString;
	if(this.startDate){
		var startDate = new Date(this.startDate);
		var startDateString = startDate.getDate() + "/" + (startDate.getMonth() + 1) + "/" + startDate.getFullYear(); // getMonth returns 0-11 so add 1 to turn into 1-12
	}
	else{
		var startDateString = "Undefined";
	}
	if(this.endDate){
		var endDate = new Date(this.endDate);
		var endDateString = endDate.getDate() + "/" + (endDate.getMonth() + 1) + "/" + endDate.getFullYear(); // getMonth returns 0-11 so add 1 to turn into 1-12
	}
	else{
		var endDateString = "Ongoing";
	}
	
	const details = document.createElement("div");
	details.setAttribute("id", this.panelId);
	details.setAttribute("class", "detailPanel");
	details.style = "display:none; border:1px solid black; padding:2px;";
	const buttonElement = document.createElement("Input");
	buttonElement.type = "button";
	buttonElement.onclick = hideParent;
	buttonElement.style = "float:right;";
	buttonElement.value = "X";
	details.appendChild(buttonElement);
	if(this.sucessor){
		const preButtonElement = document.createElement("Input");
		preButtonElement.setAttribute("missiondetailpanel", this.sucessor);
		preButtonElement.type = "button";
		preButtonElement.onclick = showMissionDetail;
		preButtonElement.style = "float:right;";
		preButtonElement.value = "Next -->";
		details.appendChild(preButtonElement);
	}
	if(this.predecessor){
		const preButtonElement = document.createElement("Input");
		preButtonElement.setAttribute("missiondetailpanel", this.predecessor);
		preButtonElement.type = "button";
		preButtonElement.onclick = showMissionDetail;
		preButtonElement.style = "float:right;";
		preButtonElement.value = "<-- Previous";
		details.appendChild(preButtonElement);
	}
	const headingElement = document.createElement("h3");
	headingElement.innerHTML = '<a href="https://en.wikipedia.org/wiki/' + this.name + '" target="wiki">' + this.name + "</a>";
	details.appendChild(headingElement);

	var t;
	var a;
	var b;
	const pElement = document.createElement("p");
	a = document.createElement("a");
	a.href = "#" + this.startDate;
	pElement.appendChild(a);
	t = document.createTextNode("Start date: " + startDateString);
	a.appendChild(t);
	b = document.createElement("br");
	pElement.appendChild(b);
	a = document.createElement("a");
	a.href = "#" + this.endDate;
	pElement.appendChild(a);
	t = document.createTextNode("End date: " + endDateString);
	a.appendChild(t);
	b = document.createElement("br");
	pElement.appendChild(b);
	t = document.createTextNode("Number of travelers: " + this.travelers.length);
	pElement.appendChild(t);
	b = document.createElement("br");
	pElement.appendChild(b);
	if(this.travelers.length > 0){
		var ol = document.createElement("ol");
		pElement.appendChild(ol);
		for(i=0;i < this.travelers.length; i++){
			var li = document.createElement("li");
			ol.appendChild(li);
			a = document.createElement("a");
			li.appendChild(a);
			a.href = "https://en.wikipedia.org/wiki/" + this.travelers[i]
			a.target = "wiki"
			a.setAttribute("travelerId", this.travelers[i])
			a.onmouseenter = highlightTraveler;
			a.onmouseleave = unHighlightTraveler;
			t = document.createTextNode(this.travelers[i]);
			a.appendChild(t);
			// Pred/Succ for travelers
			var tGroup = document.getElementById(this.travelers[i]);
			var tLines = tGroup.children;
			// Iterate through traveler lines
			for(var j=0; j<tLines.length; j++){
				var lineMDPRef = tLines[j].getAttribute("missiondetailpanel");
				if(lineMDPRef == this.panelId){
					var sucLine = tLines[j].nextElementSibling;
					if(sucLine){
						sucMDPRef = sucLine.getAttribute("missiondetailpanel");
						const preButtonElement = document.createElement("Input");
						preButtonElement.setAttribute("missiondetailpanel", sucMDPRef);
						preButtonElement.type = "button";
						preButtonElement.onclick = showMissionDetail;
						preButtonElement.style = "float:right;";
						preButtonElement.value = ">";
						li.appendChild(preButtonElement);
					}
					var preLine = tLines[j].previousElementSibling;
					if(preLine){
						preMDPRef = preLine.getAttribute("missiondetailpanel");
						const preButtonElement = document.createElement("Input");
						preButtonElement.setAttribute("missiondetailpanel", preMDPRef);
						preButtonElement.type = "button";
						preButtonElement.onclick = showMissionDetail;
						preButtonElement.style = "float:right;";
						preButtonElement.value = "<";
						li.appendChild(preButtonElement);
					}
				}
			}
		}
	}
	t = document.createTextNode("Number of craft: " + this.craft.length);
	pElement.appendChild(t);
	b = document.createElement("br");
	pElement.appendChild(b);	
	if(this.craft.length > 0){
		var ol = document.createElement("ol");
		pElement.appendChild(ol);
		for(i=0;i < this.craft.length; i++){
			var li = document.createElement("li");
			ol.appendChild(li);
			t = document.createTextNode(this.craft[i]);
			li.appendChild(t);
			// Pred/Succ for craft
			var cGroup = document.getElementById(this.craft[i]);
			var cLines = cGroup.children;
			// Iterate through craft lines
			for(var j=0; j<cLines.length; j++){
				var lineMDPRef = cLines[j].getAttribute("missiondetailpanel");
				if(lineMDPRef == this.panelId){
					var sucLine = cLines[j].nextElementSibling;
					if(sucLine){
						sucMDPRef = sucLine.getAttribute("missiondetailpanel");
						const preButtonElement = document.createElement("Input");
						preButtonElement.setAttribute("missiondetailpanel", sucMDPRef);
						preButtonElement.type = "button";
						preButtonElement.onclick = showMissionDetail;
						preButtonElement.style = "float:right;";
						preButtonElement.value = ">";
						li.appendChild(preButtonElement);
					}
					var preLine = cLines[j].previousElementSibling;
					if(preLine){
						preMDPRef = preLine.getAttribute("missiondetailpanel");
						const preButtonElement = document.createElement("Input");
						preButtonElement.setAttribute("missiondetailpanel", preMDPRef);
						preButtonElement.type = "button";
						preButtonElement.onclick = showMissionDetail;
						preButtonElement.style = "float:right;";
						preButtonElement.value = "<";
						li.appendChild(preButtonElement);
					}
				}
			}
		}
	}

	details.appendChild(pElement);
	return details;
}

// Class skeleton - mission panel skeleton	// Mission panel skeleton
function skeleton(XMLSkeleton){
	this.written = 0;		// Flag to indicate whether or not a skeleton has been written into the document
	this.sequence = null;
	// Initialise these as they won't necessarily get values
	this.panelId = null;
	this.startDate = null;
	this.endDate = null;
	this.sucessor = null;
	this.predecessor = null;
	this.createDetailPanel = createMissionDetailPanelFromSkeleton;
	// Read attributes
	var attributes = XMLSkeleton.attributes;
	var n = attributes.length;
	for(var i=0; i<n; i++){
		switch(attributes[i].nodeName){
			case "name":
				this.name = attributes[i].nodeValue;
			break;
			case "sdate":
				this.startDate = attributes[i].nodeValue;
			break;
			case "edate":
				this.endDate = attributes[i].nodeValue;
			break;
			case "pid":
				this.panelId = attributes[i].nodeValue;
			break;
			case "pre":
				this.predecessor = attributes[i].nodeValue;
			break;
			case "suc":
				this.sucessor = attributes[i].nodeValue;
			break;
			}
	}
	// Read child nodes
	this.travelers = [];
	this.craft = [];
	var children = XMLSkeleton.childNodes;
	var n = children.length;
	for(var i=0;i<n;i++){
		if(children[i].nodeType == 1){		// Element, there are two elements, cr for craft and tv for traveler
			switch(children[i].localName){
				case "cr":
					this.craft.push(children[i].textContent);
				break;
				case "tv":
					this.travelers.push(children[i].textContent);
				break;
			}
		}
	}
}

// Function to do some drawing after the initial document load
// The idea here is that the page loads and the user gets to start using it but some extra bits come later
function completeDraw(){
	// Add event handlers to lines
	craftLayer = document.getElementById("craftLayer");
	var l = craftLayer.children.length;
	for(var i=0; i<l; i++){
		var l2 = craftLayer.children[i].children.length;
		for(var j=0; j<l2; j++){
			var line = craftLayer.children[i].children[j];
			line.onclick = showMissionDetail;
			line.onmouseenter = showLineOnly;
			line.onmouseleave = hideLineOnly;
		}
	}
	travelerLayer = document.getElementById("travelerLayer");
	var l = travelerLayer.children.length;
	for(var i=0; i<l; i++){
		var l2 = travelerLayer.children[i].children.length;
		for(var j=0; j<l2; j++){
			var line = travelerLayer.children[i].children[j];
			line.onclick = showMissionDetail;
			line.onmouseenter = showLineOnly;
			line.onmouseleave = hideLineOnly;
		}
	}
	// Draw vertical gridlines
	// There are tens of thousands of these, so it makes sense to create the SVG elements after the page has loaded, after all, they're not terribly interesting.
	var keyDates = [];
	var textElements = document.getElementsByTagName("text");
	var l = textElements.length;
	// First of all read data from all of the date text elements. These provide a mapping between the absolute date and the pixel position within the SVG.
	for(var i=0; i<l; i++){
		var key = [];
		key[0] = Date.parse(textElements[i].getAttribute("id"));
		key[1] = Number(textElements[i].getAttribute("x")) + 5;		// Text element is 10 wide so is offset to the left by 5
		keyDates.push(key);
	}
	var gridLinesLayer = document.getElementById("gridLinesLayer");
	const MSperDay = 1000 * 24 * 60 * 60;
	const dayWidth = 10;		// Needs to be the same as in the python script that drew the mission lines.
	// Now draw the first date, this one has no predecessor to consider.
	drawDateLine(keyDates[0][1], gridLinesLayer)
	for(var i=1; i<l; i++){
		// Calculate the number of days that have elapsed since the last text date. Draw that many lines between then and now.
		var diff = keyDates[i][0] - keyDates[i-1][0];
		var daysDiff = diff / MSperDay;
 		for(var j=0;j < daysDiff; j++){
			drawDateLine(keyDates[i][1] - (j * dayWidth), gridLinesLayer);
		}
	}
	
	// Parse mission state skeleton xml
	var xmlSkeletons = document.getElementsByTagName("ms");
	var skeletons = xmlSkeletons.length;
	for(var i=0;i<skeletons;i++){
		var thisSkeleton = new skeleton(xmlSkeletons[i]);
		skeletonList.push(thisSkeleton);
	}
}