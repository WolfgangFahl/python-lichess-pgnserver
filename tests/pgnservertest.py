'''
Created on 2019-12-22

@author: wf
'''
from unittest import TestCase
from flask_webtest import TestApp
from pgnserver.pgnserver import app, Game
import chess.pgn
import io
import os

class PgnServerTest(TestCase):
    """ test the PGN relay application """
    def setUp(self):
        self.app=app
        self.w=TestApp(self.app)
        self.debug=True
        pass
    
    def test(self):
        r=self.w.get('/game/cpOszEMY')
        self.assertEqual(r.status,"200 OK")
        game=chess.pgn.read_game(io.StringIO(r.text))
        self.assertEqual(14,len(game.headers))
        self.assertEqual("Play Chess With a WebCam",game.headers["Event"])
        if self.debug:
            print (game)
            
    def assureRemoved(self,gameid):        
        game=Game(gameid)
        self.assertFalse(game.lichess)
        if os.path.isfile(game.pgnfile):
            os.remove(game.pgnfile)
        return game    
        
    def testPostNew(self):
        # use a non lichess gameId
        game=self.assureRemoved('abcdefg')
        r=self.w.post('/game/'+game.gameid,{'pgn':'e4','gameid':game.gameid})
        self.assertEqual(r.template,"index.html")
        self.assertTrue(os.path.isfile(game.pgnfile))
        
    def testUpdate(self):
        game=self.assureRemoved('game000')
        r=self.w.post('/game/'+game.gameid,{'pgn':'e4','gameid':game.gameid})   
        self.assertEqual(r.status,"200 OK") 
        self.assertTrue(os.path.isfile(game.pgnfile))
        r=self.w.get('/game/'+game.gameid,{'update':''})
        self.assertEqual(r.status,"200 OK")
        self.assertEqual(r.template,"index.html")
        r=self.w.get('/game/'+game.gameid)
        self.assertEqual(r.status,"200 OK")
        self.assertTrue("1. e4" in r.text)    
        
    def testIllegal(self):
        game=self.assureRemoved('spam')
        r=self.w.post('/game/'+game.gameid,{'pgn':'This is a spam message','gameid':game.gameid})
        self.assertEqual(r.template,"index.html")
        game=Game(game.gameid)
        pgn="""[Event "?"]
[Site "?"]
[Date "????.??.??"]
[Round "?"]
[White "?"]
[Black "?"]
[Result "*"]

*"""
        self.assertEqual(pgn,game.pgn)
        #self.assertFalse(os.path.isfile(game.pgnfile))
        