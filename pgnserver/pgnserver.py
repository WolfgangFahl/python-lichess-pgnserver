from flask import Flask,request,render_template,abort
from pathlib import Path
import chess.pgn
import logging
import argparse
import io
import os
import sys
import lichess.api
from lichess.format import PGN

class Environment:
    """ Runtime Environment """
    def __init__(self):
        """ get the directory in which the script resides """
        self.scriptPath = Path(__file__).parent
        self.projectPath = self.scriptPath.parent
        self.dataPath=Path(self.projectPath, 'data')
        self.datadir=str(self.dataPath)
        Environment.checkDir(self.datadir)
        
    @staticmethod    
    def checkDir(path):    
        #print (path)
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
            except OSError:
                print ("Creation of the directory %s failed" % path)
            else:
                print ("Successfully created the directory %s " % path)      

class Args:
    """ Command Line argument handling """

    def __init__(self,argv):
        self.parser = argparse.ArgumentParser(description=argv[0])
        self.parser.add_argument('--debug',
                                 action='store_true',
                                 help="show debug output")
        self.parser.add_argument('--port',
                                 type=int,
                                 default="8033",
                                 help="port to run server at")

        self.parser.add_argument('--host',
                                 default="0.0.0.0",
                                 help="host to allow access for")

        self.args=self.parser.parse_args(argv[1:])
        
class Game:
    """ Lichess game based on Portabel Game notation """
    def __init__(self,gameid):
        self.debug=False
        self.gameid=gameid
        self.pgnfile=env.datadir+"/%s.pgn" % (gameid)
        self.pgn=None
        # if there is a local file for the game we use it
        if os.path.isfile(self.pgnfile):
            pgn=self.file_get_contents(self.pgnfile)
            self.lichess=False
        else:
            # otherwise we assume the game is available on li chess
            try: 
                pgn=lichess.api.game(self.gameid, format=PGN)
                self.lichess=True
            except Exception as error:
                # if not then this is an unknown, maybe new game
                self.error=error
                pgn=None
                self.lichess=False
        self.update(pgn)                
                
    def pgn2game(self,pgn):
        self.game=chess.pgn.read_game(io.StringIO(pgn))
        return self.game            
            
    def update(self,pgn):
        if pgn is None:
            self.pgn=None
            return 
        # ignore games from lichess
        if self.lichess:
            self.pgn=pgn
            return
        game=self.pgn2game(pgn) 
        if game.errors is not None:
            if self.debug:
                print ("game %s has errors: %s",self.gameid,game.errors)
        if game is not None:
            self.pgn=str(game)
            with open(self.pgnfile,'w') as f:
                f.write(self.pgn)
                f.close()          
    
    def file_get_contents(self,filename):
        with open(filename) as f:
            return f.read()

env=Environment()
# prepare the RESTful application
# prepare static webserver
# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='',
            static_folder=str(env.projectPath) + '/web')

app.logger.setLevel(logging.INFO)

defaultWidth=800
def index(game):
    widthStr = request.args.get('width')
    if widthStr is not None:
        width=int(widthStr)
        # minimum width is 360
        width=max(width,360)
        # maximum width 
        width=min(width,2048)
    else:
        width=defaultWidth    
    action='/game/'+game.gameid
    return render_template('index.html',gameid=game.gameid,action=action,pgn=game.pgn,width=width,height=width*397//640)

@app.route("/")
def root():
    game=Game('cpOszEMY')
    return index(game)

@app.route("/game/<gameid>",methods=['POST','GET'])
def gameRequest(gameid):
    game=Game(gameid)
    if request.method == 'GET':
        update=request.args.get('update')
        if update is not None:
            return index(game)
        """return the PGN for <gameid>"""
        if game.pgn is None:
            abort(404)
        else:    
            return game.pgn
    elif request.method == 'POST':
        """update the PGN for <gameid>"""
        formdata=request.form
        pgn=formdata['pgn']
        gameid=formdata['gameid']
        if gameid==game.gameid:
            game.update(pgn)
        else:
            game=Game(gameid)
            game.update(pgn)    
    return index(game)

if __name__ == '__main__':
    args = Args(sys.argv).args
    if args.debug:
        app.logger.setLevel(logging.DEBUG)
    app.run(port='%d' % (args.port), host=args.host, threaded=True)
