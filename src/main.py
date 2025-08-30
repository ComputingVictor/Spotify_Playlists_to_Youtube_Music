#!/usr/bin/env python3
"""
Spotify to YouTube Music Playlist Migrator

A comprehensive tool for migrating playlists from Spotify to YouTube Music
with OAuth2 authentication support for both services.

Author: Your Name
License: MIT
Version: 0.1.0
"""
import os
import json
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import dotenv

# Load environment variables from .env
dotenv.load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic

class SpotifyToYTMusicMigrator:
    """
    Main class for migrating playlists from Spotify to YouTube Music.
    
    This class handles the authentication to both services and provides
    methods to migrate playlists while preserving metadata and handling
    API rate limits appropriately.
    
    Attributes:
        spotify (spotipy.Spotify): Authenticated Spotify client instance
        ytmusic (YTMusic): Authenticated YouTube Music client instance
    """
    
    def __init__(self) -> None:
        """Initialize the migrator with empty client instances."""
        self.spotify: Optional[spotipy.Spotify] = None
        self.ytmusic: Optional[YTMusic] = None
        
    def setup_spotify(self, client_id: Optional[str] = None, 
                     client_secret: Optional[str] = None, 
                     redirect_uri: Optional[str] = None) -> None:
        """
        Configure Spotify authentication using credentials from .env or provided directly.
        
        Args:
            client_id: Spotify application client ID
            client_secret: Spotify application client secret  
            redirect_uri: OAuth redirect URI (defaults to localhost:8888/callback)
            
        Raises:
            ValueError: If authentication fails or credentials are invalid
        """
        print("Setting up connection with Spotify...")
        
        # Use credentials from .env if not provided
        client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
        
        # Verify that we have the necessary credentials
        if not client_id or not client_secret:
            print("No Spotify credentials found. Please provide them manually.")
            client_id = client_id or input("\nEnter your Spotify Client ID: ")
            client_secret = client_secret or input("Enter your Spotify Client Secret: ")
            redirect_uri = redirect_uri or input("Enter your Redirect URI (default: http://localhost:8888/callback): ") or "http://localhost:8888/callback"
            
            # Ask if user wants to save the credentials
            if input("\nDo you want to save these credentials for future use? (y/n): ").lower() == 'y':
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
        print("Connection with Spotify established.")
        
    def setup_ytmusic(self) -> None:
        """
        Configure authentication with YouTube Music using OAuth2 tokens.
        
        This method attempts to authenticate using various methods in order:
        1. oauth.json file with OAuth2 tokens
        2. ytmusic_headers.json file with HTTP headers
        3. Other authentication files
        
        Raises:
            ValueError: If no valid authentication file is found
        """
        print("\nSetting up connection with YouTube Music...")
        
        # Check if oauth.json file exists
        oauth_file = "oauth.json"
        if os.path.exists(oauth_file):
            try:
                # Try to use the oauth.json file
                print("Found oauth.json file, verifying format...")
                
                # Read file to verify its format
                with open(oauth_file, 'r') as f:
                    oauth_data = json.load(f)
                
                # Check if it's an OAuth2 file with tokens
                if 'access_token' in oauth_data and 'refresh_token' in oauth_data:
                    print("Detected OAuth2 format with tokens.")
                    
                    # Create a file in a format compatible with ytmusicapi
                    headers_file = "ytmusic_headers.json"
                    self.create_ytmusic_headers_from_oauth(oauth_data, headers_file)
                    
                    # Use the created file
                    self.ytmusic = YTMusic(headers_file)
                    print(f"✅ Connection established using credentials from {oauth_file}")
                else:
                    # If it doesn't have tokens, try to use it directly
                    self.ytmusic = YTMusic(oauth_file)
                    print(f"✅ Connection established using {oauth_file}")
                return
            except Exception as e:
                print(f"Error loading {oauth_file}: {e}")
                print("Trying alternative methods...")
        
        # Try with other authentication files
        auth_files = ["ytmusic_headers.json", "headers_auth.json", "browser_headers.json"]
        for file in auth_files:
            if os.path.exists(file):
                try:
                    self.ytmusic = YTMusic(file)
                    print(f"✅ Connection established using the file {file}")
                    return
                except Exception as e:
                    print(f"Error loading {file}: {e}")
        
        print("❌ No valid authentication file found.")
        print("Make sure you have a valid oauth.json file in the same folder as this script.")
        raise ValueError("Could not establish connection with YouTube Music.")
    
    def create_ytmusic_headers_from_oauth(self, oauth_data: Dict[str, Any], 
                                         output_file: str) -> None:
        """
        Create a headers file compatible with ytmusicapi from OAuth2 data.
        
        Args:
            oauth_data: Dictionary containing OAuth2 tokens and metadata
            output_file: Path where the headers file should be created
        """
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
        
        print(f"Created {output_file} file from OAuth2 tokens")
    
    def save_credentials_to_env(self, **credentials: str) -> None:
        """
        Save credentials to the .env file for future use.
        
        Args:
            **credentials: Key-value pairs of credentials to save
        """
        env_path = Path('.env')
        
        # Read the existing .env file if it exists
        env_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
        
        # Update existing variables or add new ones
        for key, value in credentials.items():
            key = key.upper()
            if f"{key}=" in env_content:
                # Replace the existing variable
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                env_content = '\n'.join(lines)
            else:
                # Add new variable
                env_content += f"\n{key}={value}"
        
        # Save the .env file
        with open(env_path, 'w') as f:
            f.write(env_content.strip())
        
        print(f"Credentials saved in the .env file")
    
    def get_spotify_playlists(self) -> List[Dict[str, Any]]:
        """
        Get all user playlists from Spotify.
        
        Returns:
            List of playlist dictionaries containing metadata like name, 
            ID, description, and track count
            
        Raises:
            spotipy.SpotifyException: If API call fails
        """
        print("\nGetting your Spotify playlists...")
        
        results = self.spotify.current_user_playlists()
        playlists = results['items']
        
        while results['next']:
            results = self.spotify.next(results)
            playlists.extend(results['items'])
        
        print(f"Found {len(playlists)} playlists.")
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Get all songs from a Spotify playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List of track dictionaries containing song metadata
            
        Raises:
            spotipy.SpotifyException: If playlist doesn't exist or API call fails
        """
        results = self.spotify.playlist_items(playlist_id)
        tracks = results['items']
        
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend(results['items'])
        
        return tracks
    
    def search_on_ytmusic(self, track: Dict[str, Any]) -> Optional[str]:
        """
        Search for a Spotify song on YouTube Music and return the video ID.
        
        Args:
            track: Spotify track dictionary containing name and artist information
            
        Returns:
            YouTube Music video ID if found, None otherwise
            
        Raises:
            Exception: If YouTube Music API search fails
        """
        track_name = track['track']['name']
        artists = [artist['name'] for artist in track['track']['artists']]
        artist_name = artists[0]  # Use the first artist for search
        
        query = f"{track_name} {artist_name}"
        
        try:
            search_results = self.ytmusic.search(query, filter="songs", limit=1)
            if search_results:
                return search_results[0]['videoId']
            return None
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return None
    
    def create_ytmusic_playlist(self, playlist_name: str, description: str) -> Optional[str]:
        """
        Create a playlist on YouTube Music and return its ID.
        
        Args:
            playlist_name: Name for the new playlist
            description: Description for the new playlist
            
        Returns:
            YouTube Music playlist ID if successful, None otherwise
            
        Raises:
            Exception: If playlist creation fails
        """
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=playlist_name,
                description=description,
                privacy_status="PRIVATE"  # Create playlists as private by default
            )
            return playlist_id
        except Exception as e:
            print(f"Error creating playlist '{playlist_name}': {e}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, video_ids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Add songs to a YouTube Music playlist.
        
        Args:
            playlist_id: YouTube Music playlist ID
            video_ids: List of YouTube Music video IDs to add
            
        Returns:
            API response status if successful, None otherwise
            
        Raises:
            Exception: If adding tracks fails
        """
        try:
            status = self.ytmusic.add_playlist_items(playlist_id, video_ids)
            return status
        except Exception as e:
            print(f"Error adding songs to playlist: {e}")
            return None
    
    def migrate_playlist(self, playlist: Dict[str, Any]) -> Optional[str]:
        """
        Migrate a complete playlist from Spotify to YouTube Music.
        
        This method handles the entire migration process:
        1. Creates a new playlist on YouTube Music
        2. Searches for each song on YouTube Music
        3. Adds found songs to the new playlist
        4. Provides progress updates and statistics
        
        Args:
            playlist: Spotify playlist dictionary containing metadata
            
        Returns:
            YouTube Music playlist ID if successful, None otherwise
            
        Raises:
            Exception: If migration fails at any step
        """
        playlist_name = playlist['name']
        playlist_id = playlist['id']
        description = f"Migrated from Spotify"
        if 'description' in playlist and playlist['description']:
            description += f": {playlist['description']}"
        
        print(f"\nMigrating playlist: {playlist_name}")
        
        # Get songs from Spotify playlist
        tracks = self.get_playlist_tracks(playlist_id)
        print(f"  - Found {len(tracks)} songs on Spotify")
        
        # Create playlist on YouTube Music
        ytmusic_playlist_id = self.create_ytmusic_playlist(playlist_name, description)
        if not ytmusic_playlist_id:
            print(f"  ❌ Could not create playlist on YouTube Music. Skipping.")
            return None
        
        # Search for each song on YouTube Music
        video_ids = []
        not_found = 0
        
        for i, track in enumerate(tracks):
            if not track['track']:  # Some tracks might be None or not have the 'track' key
                continue
                
            print(f"  - Processing [{i+1}/{len(tracks)}]: {track['track']['name']} - {track['track']['artists'][0]['name']}", end="")
            
            video_id = self.search_on_ytmusic(track)
            if video_id:
                video_ids.append(video_id)
                print(" ✓")
            else:
                not_found += 1
                print(" ❌")
            
            # Add songs in batches of 50 (API limit) or at the end
            if len(video_ids) == 50 or i == len(tracks) - 1:
                if video_ids:
                    status = self.add_tracks_to_playlist(ytmusic_playlist_id, video_ids)
                    if status:
                        print(f"  - Added {len(video_ids)} songs to YouTube Music")
                    video_ids = []  # Reset the list for the next batch
            
            # Small pause to avoid overloading the APIs
            time.sleep(0.5)
        
        print(f"  ✅ Playlist migrated: {playlist_name}")
        print(f"  - Songs found: {len(tracks) - not_found} out of {len(tracks)}")
        
        return ytmusic_playlist_id
    
    def migrate_all_playlists(self) -> List[Dict[str, Union[str, Optional[str]]]]:
        """
        Migrate all user playlists with interactive selection.
        
        Displays all available playlists and allows the user to select
        which ones to migrate. Provides detailed progress and summary.
        
        Returns:
            List of migration results containing playlist names and IDs
            
        Raises:
            Exception: If playlist retrieval or migration fails
        """
        playlists = self.get_spotify_playlists()
        
        # Show available playlists
        print("\nAvailable playlists:")
        for i, playlist in enumerate(playlists):
            print(f"{i+1}. {playlist['name']} ({playlist['tracks']['total']} songs)")
        
        # Ask which playlists to migrate
        selection = input("\nWhich playlists do you want to migrate? (numbers separated by commas, 'all' for all): ")
        
        selected_playlists = []
        if selection.lower() == 'all':
            selected_playlists = playlists
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
                selected_playlists = [playlists[idx] for idx in indices if 0 <= idx < len(playlists)]
            except:
                print("Invalid selection. Exiting.")
                return
        
        # Migrate the selected playlists
        results = []
        for playlist in selected_playlists:
            ytmusic_playlist_id = self.migrate_playlist(playlist)
            results.append({
                'spotify_name': playlist['name'],
                'ytmusic_id': ytmusic_playlist_id
            })
        
        # Show summary
        print("\n=== Migration Summary ===")
        print(f"Playlists migrated: {len([r for r in results if r['ytmusic_id']])}/{len(selected_playlists)}")
        
        return results

def main() -> None:
    """
    Main entry point for the Spotify to YouTube Music migration tool.
    
    This function orchestrates the entire migration process:
    1. Checks for existing credentials
    2. Sets up authentication for both services
    3. Initiates the playlist migration process
    4. Handles errors and provides user feedback
    
    Raises:
        Exception: If authentication or migration fails
    """
    print("=== Spotify to YouTube Music Playlist Migrator ===")
    print("This tool will help you migrate your playlists from Spotify to YouTube Music.")
    
    # Check if we have saved credentials
    if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"):
        print("\nSpotify credentials found in the .env file.")
    else:
        print("\nPrerequisites:")
        print("1. You need to create an application in the Spotify Developer Dashboard:")
        print("   https://developer.spotify.com/dashboard/applications")
        print("2. Once created, you will get the Client ID and Client Secret")
        print("3. In the application settings, add http://localhost:8888/callback as a Redirect URI")
    
    print("4. Make sure you have a valid oauth.json file for YouTube Music")
    
    migrator = SpotifyToYTMusicMigrator()
    
    try:
        # Set up connections
        migrator.setup_spotify()
        migrator.setup_ytmusic()
        
        # Start migration
        migrator.migrate_all_playlists()
        
        print("\nMigration completed!")
        print("You can access your migrated playlists on YouTube Music.")
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        print("Please verify your credentials and try again.")

if __name__ == "__main__":
    main()