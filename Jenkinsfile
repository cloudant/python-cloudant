// Define the test routine for different python versions

def test_python_basic(pythonVersion)
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
                export RUN_BASIC_AUTH_TESTS=1
                export CLOUDANT_ACCOUNT=\$DB_USER
                # Temporarily disable the _db_updates tests pending resolution of case 71610
                export SKIP_DB_UPDATES=1
                pip install -r requirements.txt
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


def test_python_cookie(pythonVersion)
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
                # Temporarily disable the _db_updates tests pending resolution of case 71610
                export SKIP_DB_UPDATES=1
                pip install -r requirements.txt
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

def test_python_iam(pythonVersion)
{
  node {
    // Unstash the source on this node
    unstash name: 'source'
    // Set up the environment and test
    withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'iam-testy023', usernameVariable: 'DB_USER', passwordVariable: 'IAM_API_KEY']]) {
      try {
        sh """  virtualenv tmp -p /usr/local/lib/python${pythonVersion}/bin/${pythonVersion.startsWith('3') ? "python3" : "python"}
                . ./tmp/bin/activate
                echo \$DB_USER
                export RUN_CLOUDANT_TESTS=1
                export CLOUDANT_ACCOUNT=\$DB_USER
                # Temporarily disable the _db_updates tests pending resolution of case 71610
                export SKIP_DB_UPDATES=1
                pip install -r requirements.txt
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
    'Python2-BASIC': {test_python_basic('2.7.12')},
    'Python3-BASIC': {test_python_basic('3.5.2')},
    'Python2-COOKIE': {test_python_cookie('2.7.12')},
    'Python3-COOKIE': {test_python_cookie('3.5.2')},
    'Python2-IAM': {test_python_iam('2.7.12')},
    'Python3-IAM': {test_python_iam('3.5.2')}
  )
}
