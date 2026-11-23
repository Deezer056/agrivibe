variable "region" {
  description = "The project's Region. The new AWS experience allows only this one."
  type        = string
  default     = "ap-southeast-2"
}

variable "name" {
  description = "Prefix for every resource name. The deploy workflows expect agrivibe."
  type        = string
  default     = "agrivibe"
}

variable "github_owner" {
  description = "GitHub user that owns the repositories allowed to deploy, as name@id."
  type        = string
  default     = "Deezer056@223597767"
}

variable "github_repos" {
  description = "Repositories (name = numeric id) whose 'course' environment may deploy (GitHub OIDC)."
  type        = map(string)
  default = {
    "agrivibe"            = "1426478425"
    "agrivibe-frontend"   = "1457838520"
    "fieldsat-mcp-server" = "1437972412"
  }
}

variable "image_tag" {
  description = "Image tag used for the first deploy. After that, deploy.yml sets the image."
  type        = string
  default     = "bootstrap"
}

variable "task_cpu" {
  description = "CPU units for the whole task (1024 = 1 vCPU), shared by the three containers."
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Memory in MiB for the whole task."
  type        = number
  default     = 2048
}