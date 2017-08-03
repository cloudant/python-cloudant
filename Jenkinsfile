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
  sh "docker inspect -f '{{.NetworkSettings.IPAddress}}' ${container.id} > hostIp"
  readFile('hostIp').trim()
}

def getEnvForSuite(name, hostIp) {
  def envVars = [
    'SKIP_DB_UPDATES=1' //Currently disabled
  ]
  switch(name) {
    case 'couchdb:1.6.1':
    case 'klaemo/couchdb:2.0.0':
      envVars.add('ADMIN_PARTY=true')
      envVars.add("DB_URL=http://${hostIp}:5984")
      break
    case 'cloudant':
      envVars.add("CLOUDANT_ACCOUNT=${env.DB_USER}")
      envVars.add('RUN_CLOUDANT_TESTS=1')
      break
    case 'ibmcom/cloudant-developer':
      envVars.add('RUN_CLOUDANT_TESTS=1')
      envVars.add('DB_USER=admin')
      envVars.add('DB_PASSWORD=pass')
      envVars.add("DB_URL=http://${hostIp}:8080")
      break
    default:
      error("Unknown test suite environment ${suiteName}")
  }
  return envVars
}

def test_python(pythonVersion, name) {
  node {
    // Add test suite specific environment variables
    if (name == 'cloudant') {
      withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'clientlibs-test', usernameVariable: 'DB_USER', passwordVariable: 'DB_PASSWORD']]) {
        test_python_exec(pythonVersion, getEnvForSuite(name, null))
      }
    } else {
      def args
      switch(name) {
        case 'couchdb:1.6.1':
        case 'klaemo/couchdb:2.0.0':
          args = '-p 5984:5984'
          break
        case 'ibmcom/cloudant-developer':
          args = '-p 8080:80'
          break
        default:
          error("Unknown container ${suiteName}")
      }
      docker.image(name).withRun(args) { container ->
        hostIp = hostIp(container)
        if (name == 'klaemo/couchdb:2.0.0') {
          // Create _users and _repliator DBs for Couch 2.0.0
          sh "curl -X PUT ${hostIp}:5984/_users"
          sh "curl -X PUT ${hostIp}:5984/_replicator"
        }
        test_python_exec(pythonVersion, getEnvForSuite(name, hostIp))
      }
    }
  }
}

// Define the test routine for different python versions
def test_python_exec(pythonVersion, envVars) {
  docker.withRegistry("https://${env.DOCKER_REGISTRY}", 'artifactory') {
    docker.image("${env.DOCKER_REGISTRY}python:${pythonVersion}-alpine").inside('-u 0') {
      // Set up the environment and test
      withEnv(envVars){
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
  def testAxes = [:]
  ['2.7', '3.6'].each { v ->
    ['couchdb:1.6.1','klaemo/couchdb:2.0.0','cloudant','ibmcom/cloudant-developer'].each { c ->
      testAxes.put("Python${v}_${c}", {test_python(v, c)})
    }
  }
  parallel(testAxes)
}
