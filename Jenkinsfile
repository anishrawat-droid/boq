pipeline {
    agent {
        docker {
            image 'docker:cli'
            args '--user 1000:984 -v /var/run/docker.sock:/var/run/docker.sock -e HOME=/tmp'
        }
    }

    environment {
        REGISTRY = '10.101.2.88:5000' 
        IMAGE_NAME = 'boq'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Build Docker Image') {
            steps {
                echo "Building image inside temporary Docker container..."
                sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ."
                sh "docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest"
            }
        }

        stage('Push to Local Registry') {
            steps {
                echo "Pushing image to local registry..."
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. The temporary container will now be automatically destroyed by Jenkins."
        }
    }
}