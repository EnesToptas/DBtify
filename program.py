from flask import Flask, render_template, redirect, url_for, \
    request, abort, flash, g, session
import sqlite3, os

app = Flask(__name__)

app.database = 'store.dat'
app.secret_key = 'topsecret!'

query_results = []

@app.route('/')
def hello():
    return render_template("index.html")

@app.route('/logout')
def logout():
	if ('uid' in session):
		session.pop('uid')
		if('artist' in session):
			session.pop('artist')
		else:
			session.pop('listener')
	return redirect(url_for('hello'))

@app.route('/listener/login', methods = ['GET','POST'])
def loginlistener():
    dd = connect_db()
    if request.method == 'POST':
        dbase = dd.cursor()
        twople = (name, email) = request.form['name'], request.form['email']
        dbase.execute("select * from listeners where username = ? and email = ?", twople)
        users = dbase.fetchall()
        if len(users):
            session['uid'] = users[0][0]
            session['listener'] = True
            
            return redirect(url_for('listener_home',id = session['uid']))
        else:
            dbase.execute("insert into listeners (username,email) values (?,?)", twople)
            dbase.execute("select id from listeners where username = ? and email = ?", twople)
            session['uid'] = dbase.fetchone()[0]
            session['listener'] = True
            dd.commit()
            
            return redirect(url_for('listener_home',id = session['uid']))
        
    return render_template("loginlist.html")

@app.route('/artist/login', methods = ['GET','POST'])
def loginartist():
    dd = connect_db()
    if request.method == 'POST':
        dbase = dd.cursor()
        twople =  (request.form['name'], request.form['surname']) 
        dbase.execute("select * from artists where name = ? and surname = ?", twople)
        users = dbase.fetchall()
        if len(users):
            session['uid'] = users[0][0]
            session['artist'] = True
            
            return redirect(url_for('artist_home',id = session['uid']))
        else:
            dbase.execute("insert into artists (name,surname) values (?,?)", twople)
            dbase.execute("select id from artists where name = ? and surname = ?", twople)
            session['uid'] = dbase.fetchone()[0]
            session['artist'] = True
            dd.commit()
            
            return redirect(url_for('artist_home',id = session['uid']))
    
    return render_template("loginart.html")

@app.route('/listener/<int:id>', methods = ['GET','POST'])
def listener_home(id): 
    if(not 'listener' in session):
        return abort(401)
    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("select username from listeners where id = ?",(id,))
    uname = dbase.fetchone()
    if(uname == None):
        return abort(404)
    if request.method == 'POST':

        if "b1" in request.form:
            return redirect(url_for('songs'))
        elif "b2" in request.form:
            return redirect(url_for('albums'))
        elif "b3" in request.form:
            return redirect(url_for('artist_list'))
        elif "b4" in request.form:
            return redirect(url_for('search'))
        else:
            return redirect(url_for('liked', id = id))

    return render_template("listener.html",username = uname[0])

@app.route('/artist/<int:id>')
def artist_home(id): 
    if(not 'artist' in session):
        return abort(401)
    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("select (name || ' ' || surname) from artists where id = ?",(id,))
    uname = dbase.fetchone()
    if(uname == None):
        
        return abort(404)
    
    return render_template("artist.html", username = uname[0], artist_id = session['uid'])

@app.route('/songs/album/<int:id>', methods = ['GET', 'POST'])
@app.route('/songs', methods = ['GET', 'POST'], defaults={'id': None})
def songs(id):
    if(not 'listener' in session):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()
    if(id == None):
        dbase.execute("""
            select songs.id, songs.title, albums.title, albums.genre, albums.id from songs
            join albums on songs.album = albums.id
            """)
    else:
        dbase.execute("""
            select songs.id, songs.title, albums.title, albums.genre, albums.id from songs
            join albums on songs.album = albums.id where albums.id = ?
            """,(id,))        
    songs = dbase.fetchall()

    if request.method == 'POST':
        song_id = list(request.form.keys())[0]
        twople = (song_id,session['uid'])
        dbase.execute("select songid from likes where songid = ? and listenerid = ?",twople)
        result = dbase.fetchone()
        if (result == None):
            dbase.execute("insert into likes (songid,listenerid) values (?,?)",twople)
        else:
            dbase.execute("delete from likes where songid = ? and listenerid = ?",twople)
        dd.commit()
        
        return redirect(url_for('songs',id = id))

    return render_template("lists.html", list = songs, likes = 1, artist = 0, home = session['uid'])

@app.route('/albums', methods = ['GET', 'POST'])
def albums():
    if(not 'listener' in session):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("""
        select albums.id, albums.title, (artists.name || ' ' || artists.surname), albums.genre, artists.id from albums
        join artists on albums.artist = artists.id
        """)
    albums = dbase.fetchall()

    if request.method == 'POST':
        album_id = list(request.form.keys())[0]

        dbase.execute("select 1 from albumlikes where albumid = ?",(album_id,))
        x = dbase.fetchone()

        if(x == None):
            dbase.execute("insert into albumlikes values(?,?)",(album_id,session['uid']))
        else:
            dbase.execute("delete from albumlikes where albumid = ? and listenerid = ?",(album_id,session['uid']))

        dd.commit()
        
        return redirect(url_for('albums'))

    return render_template("lists.html", list = albums, likes = 1, artist = 1, home = session['uid'])

@app.route('/albums/<int:id>', methods = ['GET'])
def albums_of_artist(id):
    if(not 'artist' in session):
        return abort(401)
    if(session['uid'] != id):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("""
        select albums.id, albums.title, (artists.name || ' ' || artists.surname), albums.genre, artists.id from albums
        join artists on albums.artist = artists.id
        where artists.id = ?
        """,(id,))
    
    albums = dbase.fetchall()

    return render_template("albums_of_artist.html", list = albums, home = session['uid'])

@app.route('/artist_list', methods = ['GET', 'POST'])
def artist_list():  
    if(not 'listener' in session):
        return abort(401)

    try:
        main_artist = artist_encoder(request.args.get('Artist'))
        if main_artist == "No such artist":
            flash(main_artist)
            main_artist = None
        else:
            main_artist = main_artist[1:-1]
    except:
        main_artist = None
    

    sorting = request.args.get('sort')
    
    dd = connect_db()
    dbase = dd.cursor()

    sql_sentence_for_listing = """
    with prev as(
        select count(*) as ll,artists from likes
        join songs on likes.SONGID = songs.ID
        group by artists),
    prevtwo as (
        select artists.ID, artists.NAME, artists.SURNAME, IFNULL(sum(prev.ll),0) as likes from artists
        left join prev on prev.artists like '%a' || artists.ID  || 'a%' 
        group by artists.id)
    """
    
    if sorting:
        dbase.execute(sql_sentence_for_listing+"select * from prevtwo order by likes desc")
    elif main_artist:
        dbase.execute(sql_sentence_for_listing+"""
            select prevtwo.id,prevtwo.name,prevtwo.surname,count(prevtwo.ID) as "Feats" from prevtwo
            join songs on (songs.artists like '%aa' || prevtwo.ID  || 'a%' or songs.artists like '%a' || prevtwo.ID  || 'aa%')
            where songs.artists like  '%a' || ? || 'a%' and prevtwo.ID != ?
            group by prevtwo.ID
            """,(main_artist,main_artist))        
    else:
        dbase.execute(sql_sentence_for_listing+"select * from prevtwo")

    artists = dbase.fetchall()
    temp = []
    for element in artists:
        address = "egg"+str(6-(element[0]-1)%6)+".png"
        element = element + (url_for('static',filename=address),)
        temp.append(element)

    return render_template("artistlist.html", list = temp, home = session['uid'], issorted = sorting, feats = main_artist)

@app.route('/artist_profile/<int:id>')
def artist_profile(id):
    if(not 'listener' in session):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("select name, surname from artists where id = ?",(id,))
    (name,surname) = dbase.fetchone()
    artist = {'name' : name + " " + surname}
    dbase.execute("""
            select count(*) from likes
            join songs on likes.SONGID = songs.ID
            where artists like '%a' || ?  || 'a%';
            """,(id,))
    artist['likes'] = dbase.fetchone()[0]    
    dbase.execute("select id, title, genre from albums where artist = ?",(id,))
    artist['albums'] = dbase.fetchall()
    dbase.execute("""
            select songs.id, songs.title, albums.title, albums.genre, albums.id from songs
            join albums on songs.album = albums.id
            where songs.artists like '%a' || ?  || 'a%'""",(id,))
    artist['songs'] = dbase.fetchall()
    artist['picture'] = "egg"+str(6-(id-1)%6)+".png"
    dbase.execute("""
            select songs.id, songs.title, albums.title, count(likes.songid) as liked, albums.id from songs
            join albums on songs.album = albums.id
            left join likes on songs.id = likes.songid
            where songs.artists like '%a' || ?  || 'a%'
            group by songs.id
            order by liked desc
            limit 10""",(id,))
    artist['liked'] = dbase.fetchall()
 
    return render_template("artistprofile.html", element = artist)

@app.route('/search',methods = ['GET','POST'])
def search():
    if(not 'listener' in session):
        return abort(401)

    where = "where "

    if request.method == 'POST':

        if 'likes' in request.form:

            song_id = list(request.form.keys())[0]
            twople = (song_id,session['uid'])
            dd = connect_db()
            dbase = dd.cursor()
            dbase.execute("select songid from likes where songid = ? and listenerid = ?",twople)
            result = dbase.fetchone()
            if (result == None):
                dbase.execute("insert into likes (songid,listenerid) values (?,?)",twople)
            else:
                dbase.execute("delete from likes where songid = ? and listenerid = ?",twople)
            dd.commit()
            
            return render_template("lists.html", list = query_results, likes = 1, artist = 0, home = session['uid'])

        dd = connect_db()
        dbase = dd.cursor()

        is_artist = request.form.get('Artist')
        is_genre = request.form.get('Genre')
        is_title = request.form.get('Box')

        if is_artist:
            is_artist = is_artist.split(' ')
            if len(is_artist) > 1:
                dbase.execute("select id from artists where name = ? and surname = ?",("".join(is_artist[0:-1]),str(is_artist[-1])))
                artist_id = dbase.fetchone()
                if artist_id != None:
                    artist_id = artist_id[0]
                    where = where + "songs.artists like '%a" + str(artist_id) +"a%'"
                else:
                    is_genre = is_title = ""
            else:
                is_genre = is_title = ""

        if is_genre:
            if is_artist:
                where = where + "and "
            where = where + "albums.genre = \"" + is_genre + "\""

        if is_title:
            if is_artist or is_genre:
                where = where + "and "
            where = where + "songs.title like '%" + str(is_title) +"%'"

        if(len(where) <= 6):
            where = "where songs.id = -1"

        dbase.execute("""
            select songs.id, songs.title, albums.title, albums.genre, albums.id from songs
            join albums on songs.album = albums.id 
            """+where)

        songs = dbase.fetchall()
        query_results = songs
        
        return render_template("lists.html", list = songs, likes = 1, artist = 0, home = session['uid'])

    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("select distinct genre from albums")
    genres = dbase.fetchall()
    
    return render_template("search.html",list = genres)

@app.route('/liked/<int:id>', methods = ['GET', 'POST'])
def liked(id):
    
    if(not 'listener' in session):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("""
        select songs.id, songs.title, albums.title, albums.genre, albums.id from songs
        join albums on songs.album = albums.id
        join likes on likes.songid = songs.id
        where likes.listenerid = ?
        """,(id,))        
    songs = dbase.fetchall()

    if request.method == 'POST':
        song_id = list(request.form.keys())[0]
        twople = (song_id,session['uid'])
        dbase.execute("select songid from likes where songid = ? and listenerid = ?",twople)
        result = dbase.fetchone()
        if (result == None):
            dbase.execute("insert into likes (songid,listenerid) values (?,?)",twople)
        else:
            dbase.execute("delete from likes where songid = ? and listenerid = ?",twople)
        dd.commit()
        
        return redirect(url_for('liked',id = id))
    
    return render_template("lists.html", list = songs, likes = 1, artist = 0, home = session['uid'])

@app.route('/edit/<int:id>', methods = ['GET','POST'])
def edit_album(id):
    
    if(not 'artist' in session):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()
    dbase.execute("select id, title, genre from albums where id = ?",(id,))
    temp = dbase.fetchone()
    
    if temp == None:
        return abort(404)

    album = {'info' : temp}
    dbase.execute("select id, title, artists from songs where album = ?",(id,))
    songs = dbase.fetchall()
    
    for j in range(len(songs)):
        artists = [word for word in songs[j][2].split("a") if word.isdigit()]

        for i in range(len(artists)):
            dbase.execute("select name || ' ' || surname from artists where id = ?",(artists[i],))
            artists[i] = dbase.fetchone()[0]

        songs[j] = (songs[j],", ".join(artists))

    album['songs'] = songs

    if request.method == 'POST':
        if 'submit_new' in request.form:
            
            flash(insert_mass_song(request.form, id))

        elif 'submit_all' in request.form:
            
            to_flash = update_album_info(request.form, id)
            for x in to_flash:
                flash(x)
            
        else:
            if 'dltalb' in request.form:
                dbase.execute("delete from albums where id = ?",(id,))
                dd.commit()
                return redirect(url_for('albums_of_artist',id = session['uid']))
            else:
                deleted_song = request.form.get('dlt')
                dbase.execute("delete from songs where id = ?",(deleted_song,))
        
            dd.commit()
        
        return redirect(url_for('edit_album',id = id))

    return render_template("edit_album.html",album = album, home = session['uid'])

@app.route('/createalbum', methods = ['GET','POST'])
def create_album():
    if(not 'artist' in session):
        return abort(401)

    dd = connect_db()
    dbase = dd.cursor()

    if request.method == 'POST':

        form = request.form

        album_id = form.get('album_id')
        album_name = form.get('album_name')
        album_genre = form.get('album_genre')

        dbase.execute("select * from albums where id = ?",(album_id,))

        if dbase.fetchone():
            flash("There is already an album with given ID")
            
            return redirect(url_for('create_album'))

        dbase.execute("insert into albums values(?,?,?,?)",(album_id,album_genre,album_name,session['uid']))
        dd.commit()
        
        flash(insert_mass_song(form, album_id))

        return redirect(url_for('create_album'))

    return render_template("createalbum.html",home = session['uid'])

def insert_mass_song(form, id):
    artists_all = []
    for feat in request.form.getlist('artists[]'):
        
        artist_encode = artist_encoder(feat)
        if artist_encode == "No such artist":
            return "No such artist"
        
        artists_all.append(artist_encode)

    songs_to_add = zip(request.form.getlist('songIDs[]'),
        request.form.getlist('titles[]'),artists_all)

    dd = connect_db()
    dbase = dd.cursor()
    
    dbase.executemany("insert or ignore into songs values(?,?,"+str(id)+",?)",songs_to_add)
    dd.commit()
    
    return "Inserted unique ids"

def update_album_info(form, id):
    dd = connect_db()
    dbase = dd.cursor()

    returned = []

    for area in form.keys():
        value = form.get(area)
        if value:
            operation = area.split("_")[0]
            to_edit = area.split("_")[1]

            if operation == "album":
                dbase.execute("update albums set title = ? where id = ?",(value,id))
                returned.append("Successfully changed album title")
            elif operation == "genre":
                dbase.execute("update albums set genre = ? where id = ?",(value,id))
                returned.append("Successfully changed album genre")
            elif operation == "song":
                dbase.execute("update songs set title = ? where id = ?",(value,int(to_edit)))
                returned.append("Successfully changed song title")
            elif operation == "artists":
                new_artists = artist_encoder(value)
                if new_artists == "No such artist":
                    returned.append("No such artist")
                else:
                    dbase.execute("update songs set artists = ? where id = ?",(new_artists,int(to_edit)))
                    returned.append("Successfully changed song's artists")
            else:
                pass

    dd.commit()
    
    return returned

def artist_encoder(feat):
    dd = connect_db()
    dbase = dd.cursor()
    
    artist_encode = ""
    list_of = feat.split(", ")
    for artist in list_of:

        artist = artist.split(" ")
        
        name = " ".join(artist[0:-1])
        surname = artist[-1]
        
        dbase.execute("select id from artists where name = ? and surname = ?",(name,surname))
        
        id_artist = dbase.fetchone()
        if id_artist == None:
            return "No such artist"
        id_artist = id_artist[0]
        
        artist_encode = artist_encode + "a"+str(id_artist)+"a"

    return artist_encode

def connect_db():
    
    if 'db' not in g:
        g.db = sqlite3.connect(app.database)

    return g.db

@app.teardown_appcontext
def teardown_db(self):
    db = g.pop('db', None)

    if db is not None:
        db.close()

if not os.path.isfile(app.database):
    with sqlite3.connect(app.database) as connection:
        c = connection.cursor()
        c.execute("""
            CREATE TABLE artists(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT NOT NULL,
                SURNAME TEXT NOT NULL
            )""") 
        c.execute("""
            CREATE TABLE listeners(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                USERNAME TEXT UNIQUE NOT NULL,
                EMAIL TEXT UNIQUE NOT NULL
            )""") 
        c.execute("""
            CREATE TABLE albums(
                ID INTEGER PRIMARY KEY,
                GENRE TEXT NOT NULL,
                TITLE TEXT NOT NULL,
                ARTIST INTEGER NOT NULL,
                FOREIGN KEY (ARTIST) REFERENCES artists(ID)
            )""") 
        c.execute("""
            CREATE TABLE songs(
                ID INTEGER PRIMARY KEY,
                TITLE TEXT NOT NULL,
                ALBUM INTEGER NOT NULL,
                ARTISTS TEXT NOT NULL,
                FOREIGN KEY (ALBUM) REFERENCES albums(ID)
            )""") 
        c.execute("""
            CREATE TABLE likes (
                SONGID INTEGER NOT NULL,
                LISTENERID INTEGER NOT NULL,
                FOREIGN KEY (SONGID) REFERENCES songs(ID),
                FOREIGN KEY (LISTENERID) REFERENCES listeners(ID)
            )""") 
        c.execute("""
            CREATE TABLE albumlikes (
                ALBUMID   INTEGER NOT NULL,
                LISTENERID    INTEGER NOT NULL,
                FOREIGN KEY (ALBUMID) REFERENCES albums(ID),
                FOREIGN KEY (LISTENERID) REFERENCES listeners(ID)
            )""") 
        c.execute("""
            CREATE TRIGGER AlbumLikeSongs
            AFTER INSERT 
            ON albumlikes
            BEGIN
                INSERT INTO likes(songid,listenerid) SELECT id,NEW.LISTENERID AS lid FROM (SELECT id FROM songs WHERE album = NEW.ALBUMID)
                WHERE not exists (SELECT 1 FROM likes WHERE songid = id AND listenerid = lid);
            END
            """) 
        c.execute("""
            CREATE TRIGGER AlbumDeletion
            AFTER DELETE
            ON albums
            BEGIN
                DELETE FROM songs WHERE ALBUM = OLD.ID;
                DELETE FROM albumlikes WHERE ALBUMID = OLD.ID;
            END
            """) 
        c.execute("""
            CREATE TRIGGER LikeDeletion
            AFTER DELETE
            ON songs
            BEGIN
                DELETE FROM likes WHERE SONGID = OLD.ID;
            END
            """)
       

app.run(port=80)
