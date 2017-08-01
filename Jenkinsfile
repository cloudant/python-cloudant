#!groovy

/*
 * Copyright © 2017 IBM Corp. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
 * except in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the
 * License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions
 * and limitations under the License.
 */

 // Get the IP of a docker container
def hostIp(container) {
  sh "docker inspect -f '{{.Node.IP}}' ${container.id} > hostIp"
  readFile('hostIp').trim()
}

// Define the test routine for different python versions
def test_python(pythonVersion)
{
  node {
    def couch
    def couchIP
    docker.withRegistry(env.DOCKER_REGISTRY, 'artifactory') {
      docker.withServer(env.DOCKER_SWARM_URL) {
        couch = docker.image('couchdb:1.6.1').run('-p 5984:5984')
        couchIP = hostIp(couch)
      }
      try {
        docker.image("python:${pythonVersion}-alpine").inside('-u 0') {
          // Set up the environment and test
          withEnv(["DB_URL=http://${couchIP}:5984", 'SKIP_DB_UPDATES=1', 'ADMIN_PARTY=true']){
            try {
            // Unstash the source in this image
            unstash name: 'source'
            sh """pip install -r requirements.txt
                  pip install -r test-requirements.txt
                  pylint ./src/cloudant
                  nosetests -w ./tests/unit --with-xunit"""
            } finally {
              // Load the test results
              junit 'nosetests.xml'
            }
          }
        }
      } finally {
        docker.withServer(env.DOCKER_SWARM_URL) {
          couch.stop()
        }
      }
    }
  }
}

// Start of build
stage('Checkout'){
  // Checkout and stash the source
  node{
    checkout scm
    stash name: 'source'
  }
}
stage('Test'){
  // Run tests in parallel for multiple python versions
  parallel(
    // Python2: {test_python('2.7')},
    Python3: {test_python('3.6')}
  )
}
