import tmdbsimple as tmdb
from neo4j import GraphDatabase
import requests.exceptions

from constants import KEY


def init_database_connexion(url_path, auth):
    return GraphDatabase.driver(url_path, auth=None)

driver = init_database_connexion("bolt://localhost:7687", None)
tmdb.API_KEY = KEY


def add_database_constraints(tx):
    
    tx.run("CREATE CONSTRAINT ON(m: Movie) ASSERT m.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT ON (g:Genre) ASSERT g.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT ON(pc: ProductionCompany) ASSERT pc.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT ON(pc: ProductionCountry) ASSERT pc.iso_3166_1 IS UNIQUE")
    tx.run("CREATE CONSTRAINT ON(sl: SpokenLanguage) ASSERT sl.iso_639_1 IS UNIQUE")
    tx.run("CREATE CONSTRAINT ON(c: Credit) ASSERT c.credit_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT ON(u: User) ASSERT u.id IS UNIQUE")



def add_movie(tx, movie, credits):

    tx.run('''
                MERGE (movie:Movie {id: $id})
                ON CREATE SET 
                    movie.budget=$budget, 
                    movie.title=$title, 
                    movie.release_date =$release_date, 
                    movie.adult=$adult, 
                    movie.status=$status, 
                    movie.tagline=$tagline, 
                    movie.video=$video, 
                    movie.vote_average=$vote_average
                                
                FOREACH(g in $genres |
                    MERGE(genre: Genre {id: g.id})
                    ON CREATE SET
                        genre.name=g.name
                    MERGE(genre)-[:HAS_GENRE]-(movie)
                )

                FOREACH( pc in $production_companies |
                    MERGE(production_company: ProductionCompany {id: pc.id})
                    ON CREATE SET
                        production_company.name= pc.name, 
                        production_company.origin_country= pc.origin_country
                    MERGE(production_company)-[:PRODUCED_BY]-(movie)
                )

                FOREACH( pc in $production_countries |
                    MERGE(production_country: ProductionCountry{iso_3166_1: pc.iso_3166_1})
                    ON CREATE SET
                        production_country.name=pc.name
                    MERGE(production_country)-[:PRODUCED_IN]-(movie)
                )

                FOREACH( language in $spoken_languages |
                    MERGE(spokenLanguage: SpokenLanguage{iso_639_1: language.iso_639_1})
                    ON CREATE SET
                        spokenLanguage.iso_639_1= language.iso_639_1, 
                        spokenLanguage.name= language.name
                    MERGE(spokenLanguage)-[:SPOKEN_LANGUAGE]-(movie)
                )
                MERGE ( credit:Credit {credit_id: movie.id} )
                MERGE (credit)-[:HAS_CREDIT]-(movie)

                FOREACH( c in $casts |
                    MERGE(cast: Cast{id: c.id})
                    ON CREATE SET 
                        cast.name= c.name,
                        cast.character= c.character, 
                        cast.order= c.order, 
                        cast.credit_id= c.credit_id, 
                        cast.cast_id= c.cast_id, 
                        cast.gender= c.gender
            
                    MERGE(cast)-[:CASTED]-(credit)
                )

                FOREACH( c in $crews |
                    MERGE(crew: Crew{id: c.id})
                    ON CREATE SET
                        crew.name= c.name,
                        crew.credit_id= c.credit_id, 
                        crew.department= c.department, 
                        crew.gender= c.gender
                        
                    MERGE(crew)-[:CREW_IN]-(credit)
                )

            
            ''',
           id=movie.id, 
           budget = movie.budget,
           title = movie.title,
           release_date = movie.release_date,
           adult = movie.adult,
           status = movie.status,
           tagline = movie.tagline,
           video = movie.video,
           vote_average = movie.vote_average,
           imdb_id=movie.imdb_id,
           original_language=movie.original_language,
           original_title=movie.original_title,
           overview=movie.overview,
           popularity=movie.popularity,
           genres=movie.genres,
           production_companies=movie.production_companies,
           production_countries=movie.production_countries,
           spoken_languages=movie.spoken_languages,
           casts=credits.cast,
           crews=credits.crew

           )
    
    

with driver.session() as session:
    session.write_transaction(add_database_constraints)
    for x in range(15000, 17000):
        try:
            movie = tmdb.Movies(x)
            response = movie.info()
            credits = tmdb.Movies(x)
            response = credits.credits()
            
            session.write_transaction(add_movie, movie, credits)
            print('added Movie with id: ' , x )
        except requests.exceptions.HTTPError:
            print('Movie with id: ' , x , ' Not Found')
            continue

        
def ignore():
    movie = tmdb.Movies(x)
    response = movie.info()

    credits = tmdb.Movies(x)
    response = credits.credits()
    casts = credits.cast
    crews = credits.crew