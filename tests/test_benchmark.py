"""Test the performance of the container implementation."""
import random

import pytest


@pytest.mark.benchmark(group='write', min_rounds=3)
def test_pack_write(temp_container, generate_random_data, benchmark):
    """Add 10000 objects to the container in packed form, and benchmark write and read speed."""
    num_files = 10000
    # Use a seed for more reproducible runs
    data = generate_random_data(num_files=num_files, min_size=0, max_size=1000, seed=42)
    data_content = list(data.values())

    hashkeys = benchmark(temp_container.add_objects_to_pack, data_content, compress=False)

    assert len(hashkeys) == len(data_content)
    # In case I have the same object more than once
    assert len(set(hashkeys)) == len(set(data_content))


@pytest.mark.benchmark(group='read')
def test_pack_read(temp_container, generate_random_data, benchmark):
    """Add 10000 objects to the container in packed form, and benchmark write and read speed."""
    num_files = 10000
    # Use a seed for more reproducible runs
    data = generate_random_data(num_files=num_files, min_size=0, max_size=1000, seed=42)
    data_content = list(data.values())

    hashkeys = temp_container.add_objects_to_pack(data_content, compress=False)

    # the length of this dict can be smaller than the length of data_content
    # if there are repeated objects
    expected_results_dict = dict(zip(hashkeys, data_content))

    random.shuffle(hashkeys)

    results = benchmark(temp_container.get_objects_content, hashkeys)

    # I use `set(data)` because if they are identical, they get the same UUID
    assert results == expected_results_dict


@pytest.mark.benchmark(group='check', min_rounds=3)
def test_has_objects(temp_container, generate_random_data, benchmark):
    """Benchmark speed to check object existence.

    Add 10000 objects to the container (half packed, half loose), and benchmark speed to check existence
    of these 10000 and of 5000 more that do not exist.
    """
    num_files_half = 5000
    # Use a seed for more reproducible runs
    data_packed = generate_random_data(num_files=num_files_half, min_size=0, max_size=1000, seed=42)
    data_content_packed = list(data_packed.values())

    hashkeys_packed = temp_container.add_objects_to_pack(data_content_packed, compress=False)

    # Different seed to get different data
    data_loose = generate_random_data(num_files=num_files_half, min_size=0, max_size=1000, seed=44)
    data_content_loose = list(data_loose.values())

    hashkeys_loose = []
    for content in data_content_loose:
        hashkeys_loose.append(temp_container.add_object(content))

    # Will contain tuples `(hashkey, exists)`` [where `exists` is a Boolean]
    existence_array = []
    for hashkey in hashkeys_packed:
        existence_array.append((hashkey, True))
    for hashkey in hashkeys_loose:
        existence_array.append((hashkey, True))
    for idx in range(num_files_half):
        existence_array.append(('UNKNOWN{}'.format(idx), False))

    # Shuffle pairs
    random.shuffle(existence_array)

    hashkeys_to_check, expected_result = zip(*existence_array)

    result = benchmark(temp_container.has_objects, hashkeys_to_check)

    # I use `set(data)` because if they are identical, they get the same UUID
    assert result == list(expected_result)