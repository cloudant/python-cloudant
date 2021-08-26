#!/usr/bin/env python
# Copyright © 2016, 2021 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module that contains exception messages for the Cloudant Python client
library.
"""
ARGUMENT_ERROR = {
    100: 'A general Cloudant argument error was raised.',
    # Client
    101: 'Invalid year and/or month supplied.  Found: year - {0}, month - {1}',
    # Database
    102: 'Invalid role(s) provided: {0}.  Valid roles are: {1}',
    103: 'Invalid index type: {0}.  Index type must be '
         'either \"json\" or \"text\".',
    104: 'A single query/q parameter is required.  Found: {0}',
    105: 'Invalid argument: {0}',
    106: 'Argument {0} is not an instance of expected type: {1}',
    # Design document
    107: 'View {0} already exists in this design doc.',
    108: 'An index with name {0} already exists in this design doc.',
    109: 'A list with name {0} already exists in this design doc.',
    110: 'A show function with name {0} already exists in this design doc.',
    111: 'View {0} does not exist in this design doc.',
    112: 'An index with name {0} does not exist in this design doc.',
    113: 'A list with name {0} does not exist in this design doc.',
    114: 'A show function with name {0} does not exist in this design doc.',
    # Feed
    115: 'Error converting argument {0}: {1}',
    116: 'Invalid argument {0}',
    117: 'Argument {0} not instance of expected type: {1}',
    118: 'Argument {0} must be > 0.  Found: {1}',
    119: 'Invalid value ({0}) for feed option.  Must be one of {1}',
    120: 'Invalid value ({0}) for style option.  Must be main_only, '
         'or all_docs.',
    121: 'Invalid infinite feed option: {0}.  Must be set to continuous.',
    # Index
    122: 'The design document id: {0} is not a string.',
    123: 'The index name: {0} is not a string.',
    124: '{0} provided as argument(s).  A JSON index requires that '
         'only a \'fields\' argument is provided.',
    125: 'Deleting an index requires a design document id be provided.',
    126: 'Deleting an index requires an index name be provided.',
    127: 'Invalid argument: {0}',
    128: 'Argument {0} is not an instance of expected type: {1}',
    # Query
    129: 'Invalid argument: {0}',
    130: 'Argument {0} is not an instance of expected type: {1}',
    131: 'No selector in the query or the selector was empty.  '
         'Add a selector to define the query and retry.',
    # View
    132: 'The map property must be a dictionary.',
    133: 'The reduce property must be a string.',
    # Common_util
    134: 'Key list element not of expected type: {0}',
    135: 'Invalid value for stale option {0} must be ok or update_after.',
    136: 'Error converting argument {0}: {1}',
    137: 'Invalid document ID: {0}',
    138: 'Invalid attachment name: {0}'
}

CLIENT = {
    100: 'A general Cloudant client exception was raised.',
    101: 'Value must be set to a Database object. Found type: {0}',
    102: 'You must provide a url or an account.',
    103: 'Invalid service: IAM API key or username/password credentials are required.',
    404: 'Database {0} does not exist. Verify that the client is valid and try again.',
    412: 'Database {0} already exists.'
}

DATABASE = {
    100: 'A general Cloudant database exception was raised.',
    101: 'Unexpected index type. Found: {0}',
    400: 'Invalid database name during creation. Found: {0}',
    401: 'Unauthorized to create database {0}',
    409: 'Document with id {0} already exists.',
    412: 'Database {0} already exists.'
}

DESIGN_DOCUMENT = {
    100: 'A general Cloudant design document exception was raised.',
    101: 'Cannot add a MapReduce view to a design document for query indexes.',
    102: 'Cannot update a query index view using this method.',
    103: 'Cannot delete a query index view using this method.',
    104: 'View {0} must be of type View.',
    105: 'View {0} must be of type QueryIndexView.',
    106: 'Function for search index {0} must be of type string.',
    107: 'Definition for query text index {0} must be of type dict.'
}

DOCUMENT = {
    100: 'A general Cloudant document exception was raised.',
    101: 'A document id is required to fetch document contents. '
         'Add an _id key and value to the document and re-try.',
    102: 'The field {0} is not a list.',
    103: 'Attempting to delete a doc with no _rev. Try running .fetch and re-try.'
}

FEED = {
    100: 'A general Cloudant feed exception was raised.',
    101: 'Infinite _db_updates feed not supported for CouchDB.'
}

INDEX = {
    100: 'A general Cloudant index exception was raised.',
    101: 'Creating the \"special\" index is not allowed.',
    102: 'Deleting the \"special\" index is not allowed.'
}

REPLICATOR = {
    100: 'A general Cloudant replicator exception was raised.',
    101: 'You must specify either a source_db Database object or a manually composed'
         ' \'source\' string/dict.',
    102: 'You must specify either a target_db Database object or a manually composed'
         ' \'target\' string/dict.',
    404: 'Replication with id {0} not found.'
}

RESULT = {
    100: 'A general result exception was raised.',
    101: 'Failed to interpret the argument {0} as a valid key value or as a valid slice.',
    102: 'Cannot use {0} when performing key access or key slicing. Found {1}',
    103: 'Cannot use {0} for iteration. Found {1}',
    104: 'Invalid page_size: {0}'
}

VIEW = {
    100: 'A general view exception was raised.',
    101: 'A QueryIndexView is not callable.  If you wish to execute a query '
         'use the database \'get_query_result\' convenience method.',
    102: 'Cannot create a custom result context manager using a '
         'QueryIndexView.  If you wish to execute a query use the '
         'database \'get_query_result\' convenience method instead.'
}
