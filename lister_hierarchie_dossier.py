# -*- coding: utf-8 -*-
import os

def lister_fichiers_dossier_courant(racine):
    #
    # Liste tous les fichiers se trouvant dans le dossier donne et dans ses sous-dossiers,
    # en ignorant le dossier 'Maxamed'.
    #
    # Args:
    #    racine (str): Chemin du dossier a explorer.

    # Returns:
    #    None
    #
    print(f"Exploration du dossier : {racine}")  # ?? Ajout debug pour verifier le chemin
    if not os.path.exists(racine):
        print("Erreur : Le chemin specifie n'existe pas.")
        return

    for dossier_racine, sous_dossiers, fichiers in os.walk(racine):
        # Exclure le dossier 'Maxamed' s'il est rencontre
        if 'Maxamed' in sous_dossiers:
            sous_dossiers.remove('Maxamed')

        niveau = dossier_racine.replace(racine, '').count(os.sep)
        indentation = ' ' * 4 * niveau
        print(f"{indentation}[Dossier] {os.path.basename(dossier_racine) or '.'}")

        for fichier in fichiers:
            indentation_fichier = ' ' * 4 * (niveau + 1)
            print(f"{indentation_fichier}- {fichier}")

# Exemple d'utilisation :
if __name__ == "__main__":
    chemin_racine = "."  # Prendre le dossier courant
    lister_fichiers_dossier_courant(chemin_racine)
