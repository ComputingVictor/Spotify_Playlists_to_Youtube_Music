#!/usr/bin/env python3
"""
Herramienta para migrar playlists de Spotify a YouTube Music
Con soporte para autenticación OAuth2
"""
import os
import json
import time
from typing import List, Dict, Any
from pathlib import Path
import dotenv

# Cargar variables de entorno desde .env
dotenv.load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic

class SpotifyToYTMusicMigrator:
    def __init__(self):
        self.spotify = None
        self.ytmusic = None
        
    def setup_spotify(self, client_id=None, client_secret=None, redirect_uri=None):
        """Configura la autenticación con Spotify usando credenciales de .env o proporcionadas"""
        print("Configurando la conexión con Spotify...")
        
        # Usar credenciales de .env si no se proporcionaron
        client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
        
        # Verificar que tenemos las credenciales necesarias
        if not client_id or not client_secret:
            print("No se encontraron credenciales de Spotify. Por favor, proporciónalas manualmente.")
            client_id = client_id or input("\nIngresa tu Spotify Client ID: ")
            client_secret = client_secret or input("Ingresa tu Spotify Client Secret: ")
            redirect_uri = redirect_uri or input("Ingresa tu Redirect URI (predeterminada: http://localhost:8888/callback): ") or "http://localhost:8888/callback"
            
            # Preguntar si desea guardar las credenciales
            if input("\n¿Deseas guardar estas credenciales para usos futuros? (s/n): ").lower() == 's':
                self.save_credentials_to_env(
                    spotify_client_id=client_id,
                    spotify_client_secret=client_secret,
                    spotify_redirect_uri=redirect_uri
                )
        
        scope = "user-library-read playlist-read-private"
        
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        ))
        print("Conexión con Spotify establecida.")
        
    def setup_ytmusic(self):
        """Configura la autenticación con YouTube Music"""
        print("\nConfigurando la conexión con YouTube Music...")
        
        # Verificar si existe el archivo oauth.json
        oauth_file = "oauth.json"
        if os.path.exists(oauth_file):
            try:
                # Intentar usar el archivo oauth.json
                print("Encontrado archivo oauth.json, verificando formato...")
                
                # Leer archivo para verificar su formato
                with open(oauth_file, 'r') as f:
                    oauth_data = json.load(f)
                
                # Verificar si es un archivo de OAuth2 con tokens
                if 'access_token' in oauth_data and 'refresh_token' in oauth_data:
                    print("Detectado formato OAuth2 con tokens.")
                    
                    # Crear un archivo de formato compatible con ytmusicapi
                    headers_file = "ytmusic_headers.json"
                    self.create_ytmusic_headers_from_oauth(oauth_data, headers_file)
                    
                    # Usar el archivo creado
                    self.ytmusic = YTMusic(headers_file)
                    print(f"✅ Conexión establecida usando credenciales de {oauth_file}")
                else:
                    # Si no tiene tokens, intentar usarlo directamente
                    self.ytmusic = YTMusic(oauth_file)
                    print(f"✅ Conexión establecida usando {oauth_file}")
                return
            except Exception as e:
                print(f"Error al cargar {oauth_file}: {e}")
                print("Intentando métodos alternativos...")
        
        # Intentar con otros archivos de autenticación
        auth_files = ["ytmusic_headers.json", "headers_auth.json", "browser_headers.json"]
        for file in auth_files:
            if os.path.exists(file):
                try:
                    self.ytmusic = YTMusic(file)
                    print(f"✅ Conexión establecida usando el archivo {file}")
                    return
                except Exception as e:
                    print(f"Error al cargar {file}: {e}")
        
        print("❌ No se encontró ningún archivo de autenticación válido.")
        print("Asegúrate de tener un archivo oauth.json válido en la misma carpeta que este script.")
        raise ValueError("No se pudo establecer conexión con YouTube Music.")
    
    def create_ytmusic_headers_from_oauth(self, oauth_data, output_file):
        """Crea un archivo de headers compatible con ytmusicapi a partir de datos OAuth2"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "X-Goog-AuthUser": "0",
            "x-origin": "https://music.youtube.com",
            "Authorization": f"{oauth_data['token_type']} {oauth_data['access_token']}"
        }
        
        with open(output_file, 'w') as f:
            json.dump(headers, f, indent=2)
        
        print(f"Creado archivo {output_file} a partir de tokens OAuth2")
    
    def save_credentials_to_env(self, **credentials):
        """Guarda las credenciales en el archivo .env"""
        env_path = Path('.env')
        
        # Leer el archivo .env existente si existe
        env_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
        
        # Actualizar variables existentes o añadir nuevas
        for key, value in credentials.items():
            key = key.upper()
            if f"{key}=" in env_content:
                # Reemplazar la variable existente
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                env_content = '\n'.join(lines)
            else:
                # Añadir nueva variable
                env_content += f"\n{key}={value}"
        
        # Guardar el archivo .env
        with open(env_path, 'w') as f:
            f.write(env_content.strip())
        
        print(f"Credenciales guardadas en el archivo .env")
    
    def get_spotify_playlists(self) -> List[Dict[str, Any]]:
        """Obtiene todas las playlists del usuario en Spotify"""
        print("\nObteniendo tus playlists de Spotify...")
        
        results = self.spotify.current_user_playlists()
        playlists = results['items']
        
        while results['next']:
            results = self.spotify.next(results)
            playlists.extend(results['items'])
        
        print(f"Se encontraron {len(playlists)} playlists.")
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Obtiene todas las canciones de una playlist de Spotify"""
        results = self.spotify.playlist_items(playlist_id)
        tracks = results['items']
        
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend(results['items'])
        
        return tracks
    
    def search_on_ytmusic(self, track: Dict[str, Any]) -> str:
        """Busca una canción de Spotify en YouTube Music y devuelve el ID"""
        track_name = track['track']['name']
        artists = [artist['name'] for artist in track['track']['artists']]
        artist_name = artists[0]  # Usar el primer artista para la búsqueda
        
        query = f"{track_name} {artist_name}"
        
        try:
            search_results = self.ytmusic.search(query, filter="songs", limit=1)
            if search_results:
                return search_results[0]['videoId']
            return None
        except Exception as e:
            print(f"Error al buscar '{query}': {e}")
            return None
    
    def create_ytmusic_playlist(self, playlist_name: str, description: str) -> str:
        """Crea una playlist en YouTube Music y devuelve su ID"""
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=playlist_name,
                description=description,
                privacy_status="PRIVATE"  # Por defecto crear playlists privadas
            )
            return playlist_id
        except Exception as e:
            print(f"Error al crear la playlist '{playlist_name}': {e}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, video_ids: List[str]):
        """Añade canciones a una playlist de YouTube Music"""
        try:
            status = self.ytmusic.add_playlist_items(playlist_id, video_ids)
            return status
        except Exception as e:
            print(f"Error al añadir canciones a la playlist: {e}")
            return None
    
    def migrate_playlist(self, playlist):
        """Migra una playlist completa de Spotify a YouTube Music"""
        playlist_name = playlist['name']
        playlist_id = playlist['id']
        description = f"Migrado desde Spotify"
        if 'description' in playlist and playlist['description']:
            description += f": {playlist['description']}"
        
        print(f"\nMigrando playlist: {playlist_name}")
        
        # Obtener canciones de la playlist de Spotify
        tracks = self.get_playlist_tracks(playlist_id)
        print(f"  - Encontradas {len(tracks)} canciones en Spotify")
        
        # Crear la playlist en YouTube Music
        ytmusic_playlist_id = self.create_ytmusic_playlist(playlist_name, description)
        if not ytmusic_playlist_id:
            print(f"  ❌ No se pudo crear la playlist en YouTube Music. Saltando.")
            return None
        
        # Buscar cada canción en YouTube Music
        video_ids = []
        not_found = 0
        
        for i, track in enumerate(tracks):
            if not track['track']:  # Algunas pistas pueden ser None o no tener la clave 'track'
                continue
                
            print(f"  - Procesando [{i+1}/{len(tracks)}]: {track['track']['name']} - {track['track']['artists'][0]['name']}", end="")
            
            video_id = self.search_on_ytmusic(track)
            if video_id:
                video_ids.append(video_id)
                print(" ✓")
            else:
                not_found += 1
                print(" ❌")
            
            # Añadir canciones por lotes de 50 (límite de la API) o al final
            if len(video_ids) == 50 or i == len(tracks) - 1:
                if video_ids:
                    status = self.add_tracks_to_playlist(ytmusic_playlist_id, video_ids)
                    if status:
                        print(f"  - Añadidas {len(video_ids)} canciones a YouTube Music")
                    video_ids = []  # Reiniciar la lista para el siguiente lote
            
            # Pequeña pausa para no sobrecargar las APIs
            time.sleep(0.5)
        
        print(f"  ✅ Playlist migrada: {playlist_name}")
        print(f"  - Canciones encontradas: {len(tracks) - not_found} de {len(tracks)}")
        
        return ytmusic_playlist_id
    
    def migrate_all_playlists(self):
        """Migra todas las playlists del usuario"""
        playlists = self.get_spotify_playlists()
        
        # Mostrar playlists disponibles
        print("\nPlaylists disponibles:")
        for i, playlist in enumerate(playlists):
            print(f"{i+1}. {playlist['name']} ({playlist['tracks']['total']} canciones)")
        
        # Preguntar qué playlists migrar
        selection = input("\n¿Qué playlists deseas migrar? (números separados por comas, 'all' para todas): ")
        
        selected_playlists = []
        if selection.lower() == 'all':
            selected_playlists = playlists
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
                selected_playlists = [playlists[idx] for idx in indices if 0 <= idx < len(playlists)]
            except:
                print("Selección inválida. Saliendo.")
                return
        
        # Migrar las playlists seleccionadas
        results = []
        for playlist in selected_playlists:
            ytmusic_playlist_id = self.migrate_playlist(playlist)
            results.append({
                'spotify_name': playlist['name'],
                'ytmusic_id': ytmusic_playlist_id
            })
        
        # Mostrar resumen
        print("\n=== Resumen de migración ===")
        print(f"Playlists migradas: {len([r for r in results if r['ytmusic_id']])}/{len(selected_playlists)}")
        
        return results

def main():
    print("=== Migrador de Playlists de Spotify a YouTube Music ===")
    print("Esta herramienta te ayudará a migrar tus playlists de Spotify a YouTube Music.")
    
    # Verificar si tenemos credenciales guardadas
    if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"):
        print("\nSe encontraron credenciales de Spotify guardadas en el archivo .env.")
    else:
        print("\nRequisitos previos:")
        print("1. Necesitas crear una aplicación en Spotify Developer Dashboard:")
        print("   https://developer.spotify.com/dashboard/applications")
        print("2. Una vez creada la aplicación, obtendrás el Client ID y Client Secret")
        print("3. En la configuración de la aplicación, añade como Redirect URI: http://localhost:8888/callback")
    
    print("4. Asegúrate de tener un archivo oauth.json válido para YouTube Music")
    
    migrator = SpotifyToYTMusicMigrator()
    
    try:
        # Configurar conexiones
        migrator.setup_spotify()
        migrator.setup_ytmusic()
        
        # Iniciar migración
        migrator.migrate_all_playlists()
        
        print("\n¡Migración completada!")
        print("Puedes acceder a tus playlists migradas en YouTube Music.")
        
    except Exception as e:
        print(f"\nError durante la migración: {e}")
        print("Por favor, verifica tus credenciales e intenta nuevamente.")

if __name__ == "__main__":
    main()