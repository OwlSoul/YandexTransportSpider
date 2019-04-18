package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"

	_ "github.com/lib/pq"
	"github.com/tidwall/gjson"
)

type Config struct {
	ListenHost  string `json:"listen_host"`
	ListenPort  int    `json:"listen_port"`
	PreloadData bool   `json:"preload_data"`

	CityName     string     `json:"city_name"`
	CenterCoords [2]float32 `json:"center_coords"`
	CenterZoom   int        `json:"center_zoom"`

	Database string `json:"database"`
	DBHost   string `json:"db_host"`
	DBPort   int    `json:"db_port"`
	DBUser   string `json:"db_user"`
	DBPass   string `json:"db_password"`

	DrawDelay      int `json:"draw_delay"`
	UpdateInterval int `json:"update_interval"`
}

type FrontendConfig struct {
	PreloadData bool `json:"preloadData"`

	CityName     string     `json:"cityName"`
	CenterCoords [2]float32 `json:"centerCoords"`
	CenterZoom   int        `json:"centerZoom"`

	DrawDelay      int `json:"drawDelay"`
	UpdateInterval int `json:"updateInterval"`
}

type DataInfo struct {
	ID         string      `json:"id"`
	Name       string      `json:"name"`
	Type       string      `json:"type"`
	Timestamp  string      `json:"timestamp"`
	StopCoords []float32   `json:"coordinates"`
	LineCoords [][]float32 `json:"lines"`
}

func loadConfig(filename string) (Config, error) {
	var config Config

	file, err := os.Open(filename)
	if err != nil {
		return config, err
	}
	decoder := json.NewDecoder(file)
	err = decoder.Decode(&config)
	if err != nil {
		return config, err
	}

	return config, nil
}

func getDataJSON(config Config) ([]byte, []DataInfo) {
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		config.DBHost, config.DBPort, config.DBUser, config.DBPass, config.Database)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		panic(err)
	}

	var sqlStatement string

	sqlStatement = `
	SELECT routes.route_id as id, routes.type, routes.name, routes.timestamp, routes.data FROM routes
	UNION
	SELECT stops.stop_id as id, 'stop', stops.name, stops.timestamp, stops.data FROM stops
	ORDER BY timestamp ASC;
	`

	rowsStop, err := db.Query(sqlStatement)
	defer rowsStop.Close()
	if err != nil {
		panic(err)
	}

	var entries []DataInfo

	for rowsStop.Next() {
		var dataID string
		var dataType string
		var dataName string
		var dataTimestamp string
		var dataBody string

		if err := rowsStop.Scan(&dataID, &dataType, &dataName, &dataTimestamp, &dataBody); err != nil {
			log.Fatal(err)
		}

		dataString := string(dataBody)

		if dataType == "stop" {
			coordX, err := strconv.ParseFloat(gjson.Get(dataString, "data.geometry.coordinates.0").String(), 32)
			if err != nil {
				coordX = 0.0
			}

			coordY, err := strconv.ParseFloat(gjson.Get(dataString, "data.geometry.coordinates.1").String(), 32)
			if err != nil {
				coordX = 0.0
			}

			var stopInfoEntry = DataInfo{
				ID:        gjson.Get(dataString, "data.properties.StopMetaData.id").String(),
				Type:      "stop",
				Name:      gjson.Get(dataString, "data.properties.StopMetaData.name").String(),
				Timestamp: dataTimestamp,
				StopCoords: []float32{
					float32(coordX),
					float32(coordY),
				},
			}
			entries = append(entries, stopInfoEntry)
		} else {
			fmt.Println("ROUTE     :", dataType, dataName)
			featureCounter := 0
			featureCondition := false
			for featureOK := true; featureOK; featureOK = !featureCondition {
				feature := gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)).String()
				if feature != "" {
					fmt.Print("FEATURE ", featureCounter, " : ")

					lineCoords := [][]float32{}

					geometryCounter := 0
					geometryCondition := false
					for geometryOK := true; geometryOK; geometryOK = !geometryCondition {
						geometryType := gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)+".features."+strconv.Itoa(geometryCounter)+".geometry.type").String()
						if geometryType == "LineString" {
							lineCounter := 0
							lineCondition := false
							for lineOK := true; lineOK; lineOK = !lineCondition {
								stringCoordX := gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)+".features."+strconv.Itoa(geometryCounter)+".geometry.coordinates."+strconv.Itoa(lineCounter)+".0").String()
								stringCoordY := gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)+".features."+strconv.Itoa(geometryCounter)+".geometry.coordinates."+strconv.Itoa(lineCounter)+".1").String()

								coordX, err := strconv.ParseFloat(stringCoordX, 32)
								if err != nil {
									coordX = 0.0
								}

								coordY, err := strconv.ParseFloat(stringCoordY, 32)
								if err != nil {
									coordX = 0.0
								}

								// Coordinates are swapped for JS Leaflet, X->Y, Y->X
								if (coordX != 0) && (coordY != 0) {
									lineCoords = append(lineCoords, []float32{float32(coordY), float32(coordX)})
								}

								lineCounter++
								lineCondition = (stringCoordX == "")
							}
						}
						geometryCounter++
						geometryCondition = (geometryType == "")
					}

					if len(lineCoords) > 0 {
						fmt.Println(len(lineCoords), "elements")

						var routeInfoEntry = DataInfo{
							ID:         gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)+".properties.ThreadMetaData.id").String(),
							Type:       gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)+".properties.ThreadMetaData.type").String(),
							Name:       gjson.Get(dataString, "data.features."+strconv.Itoa(featureCounter)+".properties.ThreadMetaData.name").String(),
							Timestamp:  dataTimestamp,
							LineCoords: lineCoords,
						}
						entries = append(entries, routeInfoEntry)
					}

				}
				featureCounter++
				featureCondition = (feature == "")
			}
			fmt.Println()
		}
	}

	resultJSON, err := json.Marshal(entries)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Data load complete!")
	fmt.Println()

	return resultJSON, entries
}

func main() {
	fmt.Println()
	fmt.Println("Yandex Spider Visualizer : STARTED")
	// Default values
	configFilename := "config/visualizer-config.json"

	fmt.Println("Loading configuratnion from ", configFilename)

	config, err := loadConfig(configFilename)
	if err != nil {
		log.Fatal(err)
	}

	if config.ListenHost == "" {
		config.ListenHost = "localhost"
	}

	if config.ListenPort == 0 {
		config.ListenPort = 9999
	}

	if config.CityName == "" {
		config.CityName = "NOT DEFINED"
	}

	fmt.Println("Configuration:")
	fmt.Println("  Listen host :", config.ListenHost)
	fmt.Println("  Listen port :", config.ListenPort)
	fmt.Println("  Preload data:", config.PreloadData)
	fmt.Println()
	fmt.Println("  City name   :", config.CityName)
	fmt.Println("  Center crds :", config.CenterCoords[0], config.CenterCoords[1])
	fmt.Println("  Center zoom :", config.CenterZoom)
	fmt.Println()
	fmt.Println("  Database    :", config.Database)
	fmt.Println("  DB Host     :", config.DBHost)
	fmt.Println("  DB Port     :", config.DBPort)
	fmt.Println("  DB User     :", config.DBUser)
	fmt.Println("  DB Password :", config.DBPass)
	fmt.Println()
	fmt.Println("  Draw delay  :", config.DrawDelay)
	fmt.Println()

	var preparedData []byte
	if config.PreloadData {
		fmt.Println("Preloading data from database...")
		fmt.Println()
		preparedData, _ = getDataJSON(config)
	}

	http.HandleFunc("/spider/data", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Println("Data JSON request!")
		if !config.PreloadData {
			fmt.Println("Getting stops from database...")
			preparedData, _ = getDataJSON(config)
		}
		w.Write(preparedData)
	})

	http.HandleFunc("/spider/config", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Println("Config JSON request!")
		frontendConfig := FrontendConfig{
			PreloadData:    config.PreloadData,
			CityName:       config.CityName,
			CenterZoom:     config.CenterZoom,
			CenterCoords:   config.CenterCoords,
			DrawDelay:      config.DrawDelay,
			UpdateInterval: config.UpdateInterval,
		}
		configJSON, _ := json.Marshal(frontendConfig)
		w.Write(configJSON)
	})

	fs := http.FileServer(http.Dir("frontend"))
	http.Handle("/", fs)

	listenAddress := config.ListenHost + ":" + strconv.Itoa(config.ListenPort)
	fmt.Println("Starting to listen on", listenAddress)
	log.Fatal(http.ListenAndServe(listenAddress, nil))

	fmt.Println("Yandex Spider Visualizer : TERMINATED")
}
