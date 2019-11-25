def getEnvForSuite(suiteName) {
  // Base environment variables
  def envVars = [
    "CLOUDANT_ACCOUNT=$DB_USER",
    "RUN_CLOUDANT_TESTS=1",
    "SKIP_DB_UPDATES=1" // Disable pending resolution of case 71610
  ]
  // Add test suite specific environment variables
  switch(suiteName) {
    case 'basic':
      envVars.add("RUN_BASIC_AUTH_TESTS=1")
      break
    case 'iam':
      // Setting IAM_API_KEY forces tests to run using an IAM enabled client.
      envVars.add("IAM_API_KEY=$DB_IAM_API_KEY")
      break
    case 'cookie':
    case 'simplejson':
      break
    default:
      error("Unknown test suite environment ${suiteName}")
  }
  return envVars
}

def setupPythonAndTest(pythonVersion, testSuite) {
  node {
    // Unstash the source on this node
    unstash name: 'source'
    // Set up the environment and test
    withCredentials([usernamePassword(credentialsId: 'clientlibs-test', usernameVariable: 'DB_USER', passwordVariable: 'DB_PASSWORD'),
                     string(credentialsId: 'clientlibs-test-iam', variable: 'DB_IAM_API_KEY')]) {
      withEnv(getEnvForSuite("${testSuite}")) {
        try {
          sh """
            virtualenv tmp -p ${pythonVersion.startsWith('3') ? "python3" : "python"}
            . ./tmp/bin/activate
            python --version
            pip install -r requirements.txt
            pip install -r test-requirements.txt
            ${'simplejson'.equals(testSuite) ? 'pip install simplejson' : ''}
            pylint ./src/cloudant
            nosetests -A 'not db or (db is "cloudant" or "cloudant" in db)' -w ./tests/unit --with-xunit
          """
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
  def py2 = '2'
  def py3 = '3'
  def axes = [:]
  [py2, py3].each { version ->
    ['basic','cookie','iam'].each { auth ->
       axes.put("Python${version}-${auth}", {setupPythonAndTest(version, auth)})
    }
  }
  axes.put("Python${py3}-simplejson", {setupPythonAndTest(py3, 'simplejson')})
  parallel(axes)
}

stage('Publish') {
  gitTagAndPublish {
    isDraft=true
    releaseApiUrl='https://api.github.com/repos/cloudant/python-cloudant/releases'
  }
}
