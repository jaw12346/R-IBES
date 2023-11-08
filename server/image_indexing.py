"""
Script to bulk-index images to the local facial recognition database.
This script can be used to index large amounts of images to the local facial recognition database.
"""

import os
import time
import sqlite3
from collections import namedtuple
from deepface import DeepFace  # Must also run `pip install tensorrt --extra-index-url https://pypi.nvidia.com`
from PIL import Image

from server import conversions
from server import local_facial_recognition as lfr

PeopleCount = namedtuple('PeopleCount', ['name', 'count', 'total_time'])


def align_face(df_face, file_location, debug=False):
    """
    Given a dataframe containing the coordinates of a face, crop the image to the face and display it
    :param df_face: Dataframe containing the coordinates of the face
    :type df_face: dict
    :param file_location: Location of the file to crop
    :type file_location: str
    :param debug: If True, show the image for 5 seconds
    :type debug: bool
    :return: Location of the cropped image
    :rtype: str
    """
    img = Image.open(file_location)
    img = img.convert('L')  # Convert img to greyscale

    # Get the coordinates of the face
    x = df_face['facial_area']['x']
    y = df_face['facial_area']['y']
    w = df_face['facial_area']['w']
    h = df_face['facial_area']['h']

    cropped = img.crop((x, y, x + w, y + h))  # Crop the image to the face
    if debug:
        cropped.show()  # Display the cropped image
        time.sleep(5)  # Show the image for 5 seconds

    # Save the cropped image
    old_name = file_location.split('/')[-1]
    new_name = f'cropped-{old_name}'
    new_location = file_location.split(old_name)[0] + new_name
    cropped.save(new_location)
    return new_location  # Return the location of the cropped image


def detect_faces(file_location, debug=False):
    """
    Given a file location, detect all faces in the image and call for the largest face in the image to be aligned
    :param file_location: Location of the file to detect faces in
    :type file_location: str
    :param debug: If True, show the image for 5 seconds and print debug statements
    :type debug: bool
    :return: The location of the cropped image
    :rtype: str or None
    """
    # face detection and alignment
    face_objs = DeepFace.extract_faces(img_path=file_location,
                                       target_size=(224, 224)
                                       )
    if face_objs is not None:
        if debug:
            print(f'Found {len(face_objs)} faces in the image.')
        best_face = face_objs[0]
        for face in face_objs:
            if face['confidence'] > best_face['confidence']:
                best_face = face
        if debug:
            print('Extracting the best face in the image.')
        cropped_path = align_face(best_face, file_location, debug)
        return cropped_path
    if debug:
        print('No faces detected in the image.')
    return None


def bulk_index(source_dir, source='user', debug=False):
    """
    Bulk index a list of images to the local facial recognition database.
    :param source_dir: Directory containing images to index.
                       Each subdirectory should be named after the person in the image.
    :type source_dir: str
    :param source: Source of the images. Default is 'user' (user provided)
                   but can also be databases such as 'lfw' (Labeled Faces in the Wild).
    :type source: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: List of namedtuples of the form (name, count) where name is the name of the person and count is the number
             of images indexed for that person.
    :rtype: namedtuple(str, int) -- PeopleCount
    """
    subdirs = get_subdirs(source_dir)
    people_count = []
    if subdirs:
        i = 1
        for this_dir in subdirs:
            start_time = time.time()
            images = [f'{this_dir}/{file_name}' for file_name in os.listdir(this_dir)]
            name = this_dir.split('/')[-1]
            indexed_images = 0
            for image in images:
                if source == 'user':
                    image = detect_faces(image, debug)
                encoding = lfr.generate_face_encoding(image, name)
                if encoding is None:
                    print(f'Error generating encoding for {image}')
                    continue
                indexed_images += 1
            total_time = time.time() - start_time
            people_count.append(PeopleCount(name, len(images), total_time))
            if debug:
                print(f'{i}/{len(subdirs)}:\tIndexed {indexed_images} images for {name} in {total_time} seconds.')
            i += 1
    else:
        start_time = time.time()
        images = [f'{source_dir}/{file_name}' for file_name in os.listdir(source_dir)]
        name = source_dir.split('/')[-1]
        indexed_images = 0
        for image in images:
            encoding = lfr.generate_face_encoding(image, name, source)
            if encoding is None:
                print(f'Error generating encoding for {image}')
                continue
            indexed_images += 1
        total_time = time.time() - start_time
        people_count.append(PeopleCount(name, len(images), total_time))
        if debug:
            print(f'Indexed {indexed_images} images for {name} in {total_time} seconds.')
    return people_count


def get_subdirs(source_dir):
    """
    Get a list of subdirectories in a directory that contain images with file types .jpg or .png.
    :param source_dir: Directory to search for subdirectories
    :type source_dir: str
    :return: List of subdirectories
    :rtype: list(str)
    """
    return [f.path for f in os.scandir(source_dir) if f.is_dir() and os.listdir(f.path) != []]


def run(source_dir, source='user', debug=False):
    """
    Run the bulk indexing process and save the results to a file.
    :param source_dir: Parent directory of the images to index
    :type source_dir: str
    :param source: Source of the images. Default is 'user' (user provided).
                   Example: "Labeled Faces in the Wild" is 'lfw'.
    :param debug: Enable debug mode
    :type debug: bool
    :return: Number of people indexed, number of images indexed, total time (sec) to index as a PeopleCount namedtuple.
    :rtype: namedtuple(int, int, float) -- PeopleCount
    """
    people_count = bulk_index(source_dir, source)
    num_people = len(people_count)
    num_images = 0
    total_time = 0
    with open('indexing_results.txt', 'w') as outfile:
        for person in people_count:
            # Name, Count, Total Time
            outfile.write(f'{person.name}\t{person.count}\t{person.total_time}\n')
            num_images += person.count  # Number of encodings saved for this person
            total_time += person.total_time  # Total time to save encodings for this person

    if debug:
        print(f'Indexed {num_images} images for {num_people} people in {total_time} seconds.')
    return PeopleCount(num_people, num_images, total_time)


def oops_insert_indices():
    """
    Method used purely for when you forget to enter the encoding count for a name in the database after a mass index.
    **Has no other use and should not be used.**
    """
    conn = sqlite3.connect('./server/hw2.db')
    cursor = conn.cursor()
    with open('indexing_results.txt', 'r') as outfile:
        lines = outfile.readlines()
        for line in lines:
            split = line.split('\t')
            name = split[0]
            normalized_name = conversions.get_normalized_name(name)
            count = int(split[1])

            cursor.execute("SELECT COUNT(*) FROM NAME_DIRECTORY WHERE NAME=?", (name,))  # Check if name exists
            row = cursor.fetchone()
            if row is not None:
                # print(f'Adding {name} to database')
                cursor.execute("UPDATE NAME_DIRECTORY SET ENCODING_COUNT=? WHERE NAME=?", (count, normalized_name))
                conn.commit()
    conn.close()


if __name__ == '__main__':
    pass
