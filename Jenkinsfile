// Define the test routine for different python versions
def test_python(pythonVersion)
{
  node {
    // Unstash the source on this node
    unstash name: 'source'
    // Set up the environment and test
    withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'clientlibs-test', usernameVariable: 'DB_USER', passwordVariable: 'DB_PASSWORD']]) {
      try {
        sh """  virtualenv tmp -p /usr/local/lib/python${pythonVersion}/bin/${pythonVersion.startsWith('3') ? "python3" : "python"}
                . ./tmp/bin/activate
                echo \$DB_USER
                export RUN_CLOUDANT_TESTS=1
                export CLOUDANT_ACCOUNT=\$DB_USER
                pip install -r requirements.txt
                pip install -r test-requirements.txt
                nosetests -w ./tests/unit --with-xunit"""
      } finally {
        // Load the test results
        junit 'nosetests.xml'
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
    Python2: {test_python('2.7.12')},
    Python3: {test_python('3.5.2')}
  )
}
