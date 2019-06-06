from pathlib import Path

class Imagery:
    def __init__(self, name):
        self.name = name
        self.flipy = False
        self.offsetx = 0
        self.offsety = 0

maxar = Imagery("maxar")   
maxar.url = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
maxar.flipy = True
maxar.offsetx = -30
maxar.offsety = 10
maxar.tiledir = Path("tiles/maxar")
maxar.tilefile = "./tiles/maxar/x{x}y{y}z{z}.jpg"
maxar.cropdir = Path("./crops/maxar")
maxar.cropfile = "./crops/maxar/lat{lat}lng{lng}z{z}.jpg"

dg = Imagery("dg")
dg.url = "https://a.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"
dg.tiledir = Path("tiles/dg")
dg.tilefile = "./tiles/dg/x{x}y{y}z{z}.jpg"
dg.cropdir = Path("crops/dg")
dg.cropfile = "./crops/dg/lat{lat}lng{lng}z{z}.jpg"