# transport-sim

Toy application for simulating and visualizing a transportation network. Persisted with a SQL database (PostgreSQL).

### Start the Database and Visualizer
```
$ docker-compose up -d --build
```
The simulation visualizer can be viewed in a browser at http://localhost:5000.

### Run the editor application
```
$ python editor/mainEditor.py
```