"""
R-IBES facial recognition benchmarking script
"""

import sqlite3
import time
import statistics
from collections import namedtuple
from alive_progress import alive_bar

import local_facial_recognition as lfr
import conversions

BenchmarkResult = namedtuple('BenchmarkResult',
                             ['match_count', 'fail_count', 'success_rate', 'compare_time'])


def get_encodings():
    """
    Get all encodings from the database.

    :return: All encodings from the database in form {name: [encoding1, encoding2, ...]}
    :rtype: dict{str, list(ndarray(128,))}
    """
    conn = sqlite3.connect('./hw2.db')
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


def stats(success_rates, avg_times, num_zero_success_rates, number_of_people, avg_non_zero_success_rates):
    """
    Calculate the statistics for the benchmark.

    :param success_rates: List of success rates for each person
    :type success_rates: list(float)
    :param avg_times: List of average times to compare all encodings for each person
    :type avg_times: list(float)
    :param num_zero_success_rates: Number of people with 0% success rate
    :type num_zero_success_rates: int
    :param number_of_people: Total number of people in the database
    :type number_of_people: int
    :param avg_non_zero_success_rates: List of success rates for each person excluding those with 0% success rates
    :type avg_non_zero_success_rates: list(float)
    :return: Average success rate, average encoding comparison time, percent of people with 0% success rate,
             and average non-zero success rate
    :rtype: float, float, float, float
    """
    average_success_rate = sum(success_rates) / len(success_rates)
    average_time = sum(avg_times) / len(avg_times)
    percent_zero_success_rates = num_zero_success_rates / number_of_people
    average_non_zero_success_rate = sum(avg_non_zero_success_rates) / len(avg_non_zero_success_rates)

    return average_success_rate, average_time, percent_zero_success_rates, average_non_zero_success_rate


def benchmark():
    """
    Benchmark the local facial recognition system.
    """
    # For person in the database, attempt to match that encoding to the correct person
    # Measure the time it takes to match each encoding and the success rate
    encodings = get_encodings()
    all_results = {}  # Name : CompareResult

    avg_times = []
    success_rates = []
    num_zero_success_rates = 0
    number_of_people = len(encodings)
    avg_non_zero_success_rates = []

    all_start = time.time()
    current_num = 1
    # total number of elements from all encodings
    with alive_bar(len(encodings), force_tty=True) as bar:  # Progress bar, force_tty=True for PyCharm
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
            avg_times.append(sum(times) / len(times))  # Average time to compare all encodings for this person
            success_rate = match_count / (match_count + fail_count)
            success_rates.append(success_rate)
            if success_rate == 0:
                num_zero_success_rates += 1
            else:
                avg_non_zero_success_rates.append(success_rate)


            all_results[name] = BenchmarkResult(match_count, fail_count, success_rate, times)
            current_num += 1
            bar()  # Update progress bar
    total_time = time.time() - all_start

    average_success_rate, average_time, percent_zero_success_rates, average_non_zero_success_rate = (
        stats(success_rates, avg_times, num_zero_success_rates,
              number_of_people, avg_non_zero_success_rates))


    with open('./benchmarks/local_facial_recognition_benchmark_results.tsv', 'w') as outfile:
        outfile.write('Name\tMatch_Count\tFail_Count\tSuccess_Rate\tCompare_Times\n')  # Header
        for name, result in all_results.items():
            outfile.write(f'{name}\t{result.match_count}\t{result.fail_count}\t{result.success_rate}\t'
                          f'{result.compare_time}\n')  # Data / rows
        outfile.write('-'*50 + '\n')

        # General statistics
        outfile.write(f'Average image search success rate (using local DB): {average_success_rate*100:.3f}%')
        outfile.write(f'\tStandard deviation: '
                      f'{statistics.stdev(success_rates, xbar=average_success_rate)*100:.3f}%')

        outfile.write(f'Percent of people with 0% success rate: {percent_zero_success_rates*100:.3f}%')
        outfile.write(f'Average image search success rate (using local DB) excluding 0% success rates: '
              f'{average_non_zero_success_rate*100:.3f}%')
        outfile.write(f'\tStandard deviation: '
                      f'{statistics.stdev(avg_non_zero_success_rates, xbar=percent_zero_success_rates)*100:.3f}%')

        outfile.write(f'Average time per image search: {average_time:.3f} seconds')
        outfile.write(f'\tStandard deviation: {statistics.stdev(avg_times, xbar=average_time):.3f}')
        outfile.write(f'Total time to compare all encodings: {total_time:.0f} seconds')

    print(f'Average image search success rate (using local DB): {average_success_rate*100:.3f}%')
    print(f'\tStandard deviation: {statistics.stdev(success_rates, xbar=average_success_rate) * 100:.3f}%')

    print(f'Percent of people with 0% success rate: {percent_zero_success_rates * 100:.3f}%')
    print(f'Average image search success rate (using local DB) excluding 0% success rates: '
          f'{average_non_zero_success_rate*100:.3f}%')
    print(f'\tStandard deviation: '
          f'{statistics.stdev(avg_non_zero_success_rates, xbar=percent_zero_success_rates)*100:.3f}%')

    print(f'Average time per image search: {average_time:.3f} seconds')
    print(f'\tStandard deviation: {statistics.stdev(avg_times, xbar=average_time):.3f}')
    print(f'Total time to compare all encodings: {total_time:.0f} seconds')


if __name__ == '__main__':
    benchmark()
