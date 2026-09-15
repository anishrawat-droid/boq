pipeline {
    agent {
        docker {
            image 'docker:cli'
            args '-v /var/run/docker.sock:/var/run/docker.sock -e HOME=/tmp'
        }
    }

    environment {
        // Replace with your actual Docker Hub username and repository name
        DOCKER_HUB_USER = 'your-dockerhub-username'
        IMAGE_NAME      = 'boq'
        IMAGE_TAG       = "${BUILD_NUMBER}"
    }

    stages {
        stage('Build Docker Image') {
            steps {
                echo "Building image inside temporary Docker container..."
                sh "docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
                sh "docker tag ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
            }
        }

        stage('Login & Push to Docker Hub') {
            steps {
                echo "Logging into Docker Hub and pushing image..."
                // Safely authenticates against Docker Hub without exposing secrets in logs
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'HUB_USER', passwordVariable: 'HUB_PASS')]) {
                    sh "echo \$HUB_PASS | docker login -u \$HUB_USER --password-stdin"
                    sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. Cleaning up temporary builder container..."
        }
    }
}