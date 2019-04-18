function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function performDataVisualization(mymap, tileLayer) {
    // Setting parameters
    $.getJSON("/spider/config", function (config) {
        console.log(config)
        $( "#city" ).text(config.cityName)

        $("#status").text("LOADING")
        $.getJSON("/spider/data", async function (data){
            console.log(data);

            // Clear all markers, leave tile layer
            mymap.eachLayer(function (layer) {
                if (layer != tileLayer) {
                mymap.removeLayer(layer);
                }
            });

            dataLength = data.length

            // Calculating routes, stops etc
            routeCounter = 0
            stopsCounter = 0

            busCounter = 0
            tramwayCounter = 0
            trolleybusCounter = 0
            minibusCounter = 0
            otherCounter = 0

            for (var i = 0; i < dataLength; i++) {
                if (data[i].type=="stop") stopsCounter++;
                else if (data != "") {
                    routeCounter++
                    switch (data[i].type) {
                        case "bus": busCounter++; break;
                        case "tramway": tramwayCounter++; break;
                        case "trolleybus": trolleybusCounter++; break;
                        case "minibus": minibusCounter++; break;
                        default: otherCounter++;
                    }
                }
            }

            $("#stops").text(stopsCounter.toString())
            $("#routes").text(routeCounter.toString())
            $("#buses-counter").text(busCounter.toString())
            $("#trolleybuses-counter").text(trolleybusCounter.toString())
            $("#tramways-counter").text(tramwayCounter.toString())
            $("#minibuses-counter").text(minibusCounter.toString())
            

            for (var i = 0; i < dataLength; i++){
                //console.log(data[i].coordinates[0], data[i].coordinates[1])

                if (data[i].type == 'stop') {
                    var circle = L.circle([data[i].coordinates[1], data[i].coordinates[0]], {
                        color: 'blue',
                        fillColor: 'blue',
                        fillOpacity: 0.5,
                        radius: 0.5
                    })
                    circle.bindPopup("<b>ID:</b> " + data[i].id + "<br>" + "<b>Name:</b>" + data[i].name)
                    circle.addTo(mymap);
                    await sleep(config.drawDelay)
                }
                else if (data[i].type != "") {
                    switch (data[i].type) {
                    case "bus":         linecolor = {color: 'green'};
                                        break;
                    case "tramway":     linecolor = {color: 'red'}
                                        break; 
                    case "trolleybus":  linecolor = {color: 'yellow'}
                                        break;
                    case "minibus":     linecolor = {color: 'purple'}
                                        break;
                    default:            linecolor = {color: 'grey'}
                    }

                    var polyLine = L.polyline(data[i].lines, linecolor)
                    polyLine.bindPopup("<b>ID: </b> " + data[i].id + "<br>" +
                                    "<b>Type: </b> " + data[i].type + "<br>" + 
                                    "<b>Name: </b>" + data[i].name)
                    polyLine.addTo(mymap)
                    await sleep(config.drawDelay)
                }
                $("#status").text("DRAWING " + i.toString() + "/" + dataLength.toString())
            }
            $("#status").text("DONE!")

            //Plan another iteration of this
            if (!config.preloadData) {
                setTimeout(function() {
                    performDataVisualization(mymap, tileLayer)
                }, config.updateInterval * 1000)
            }
        });
    })
}

async function executeVisualization() {
    // Create map
    $.getJSON("/spider/config", function (config) {
        $( "#city" ).text(config.cityName)

        var mymap = L.map('mapid').setView([config.centerCoords[0], config.centerCoords[1]], config.centerZoom);

        tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            })
            
        tileLayer.addTo(mymap);
        
        performDataVisualization(mymap, tileLayer);;
    })
}

executeVisualization()