#!/usr/bin/env python
# Copyright (c) 2016 IBM. All rights reserved.
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
CLIENT = {
    100: 'A general Cloudant client exception was raised.',
    101: 'Value must be set to a Database object. Found type: {0}.',
    102: 'You must provide a url or an account.',
    404: 'Database {0} does not exist. Verify that the client is valid and try again.',
    409: 'Database {0} already exists.'
}

DATABASE = {
    100: 'A general Cloudant database exception was raised.',
    101: 'Unexpected index type. Found: {0}.',
    400: 'Invalid database name during creation. Found: {0}',
    401: 'Unauthorized to create database {0}.',
    409: 'Document with id {0} already exists.'
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
    102: 'Cannot use {0} when performing key access or key slicing. Found {1}.',
    103: 'Cannot use {0} for iteration. Found {1}.',
    104: 'Invalid page_size: {0}'
}
