import sqlite3
import time
from collections import namedtuple

import server.local_facial_recognition as lfr
import server.conversions as conversions


BenchmarkResult = namedtuple('BenchmarkResult',
                             ['match_count', 'fail_count', 'success_rate', 'compare_time'])


def get_encodings():
    conn = sqlite3.connect('./server/hw2.db')
    cursor = conn.cursor()
    if conn:
        # Get all encodings from the database
        query = "SELECT NAME, ENCODING FROM NAME_ENCODING"
        cursor.execute(query)
        conn.commit()
        rows = cursor.fetchall()
        conn.close()

        encodings = {}
        for row in rows:
            this_name = row[0]
            this_encoding = conversions.decode_memoryview_to_ndarray(row[1])
            if this_name in encodings:
                encodings[this_name].append(this_encoding)
            else:
                encodings[this_name] = [this_encoding]
        return encodings
    return None


def benchmark():
    """
    Benchmark the local facial recognition system.
    """
    # For person in the database, attempt to match that encoding to the correct person
    # Measure the time it takes to match each encoding and the success rate
    encodings = get_encodings()
    all_results = {}  # Name : CompareResult

    lowest_success_rate = 1
    lowest_success_person = ''
    highest_success_rate = 0
    highest_success_person = ''

    all_start = time.time()
    current_num = 1
    # total number of elements from all encodings
    for name in encodings:
        match_count = 0
        fail_count = 0
        person_encodings = encodings[name]
        times = []
        for encoding in person_encodings:
            # For each encoding, compare it to every other encoding in the database
            start_time = time.time()
            determined_person = lfr.identify_person_from_encoding(encoding)
            if determined_person == name:
                match_count += 1
            else:
                fail_count += 1
            comparison_time = time.time() - start_time
            times.append(comparison_time)
        success_rate = match_count / (match_count + fail_count)
        if success_rate < lowest_success_rate:
            lowest_success_rate = success_rate
            lowest_success_person = name
        if success_rate > highest_success_rate:
            highest_success_rate = success_rate
            highest_success_person = name

        all_results[name] = BenchmarkResult(match_count, fail_count, success_rate, times)
        print(f'{current_num} / {len(encodings)} -- {(time.time() - all_start):.0f} seconds total')
        current_num += 1
    total_time = time.time() - all_start

    with open('local_facial_recognition_benchmark_results.txt', 'w') as f:
        for name in all_results:
            result = all_results[name]
            f.write(f'{name}\t{result.match_count}\t{result.fail_count}\t{result.success_rate}\t{result.compare_time}\n')
        f.write('-'*50 + '\n')
        f.write(f'Lowest success rate: {lowest_success_rate:.5f}% ({lowest_success_person})\n')
        f.write(f'Highest success rate: {highest_success_rate:.5f}% ({highest_success_person})\n')
        f.write(f'Total time to compare all encodings: {total_time:.0f} seconds\n')

    print(f'Lowest success rate: {lowest_success_rate:.5f}% ({lowest_success_person})')
    print(f'Highest success rate: {highest_success_rate:.5f}% ({highest_success_person})')
    print(f'Total time to compare all encodings: {total_time:.0f} seconds')


if __name__ == '__main__':
    benchmark()
