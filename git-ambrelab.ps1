# ============================================================
# Configuration du dépôt AmbreLab
# ============================================================

$RepoUrl = "https://github.com/Barrimen/AmbreLab.git"
$RepoName = "AmbreLab"

$GitUserName = "Barrimen"
$GitUserEmail = "jfbigeard@gmail.com"

# Chemin réel du dépôt déjà cloné
$RepoDirectory = "C:\Users\Barrimen\OneDrive\JDR\#AmbreLab\Architecture - Github"

function Write-Title {
    Clear-Host
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host " Gestion du dépôt GitHub : $RepoName" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Pause-Script {
    Write-Host ""
    Read-Host "Appuie sur Entrée pour continuer"
}

function Test-GitInstalled {
    $GitCommand = Get-Command git -ErrorAction SilentlyContinue

    if (-not $GitCommand) {
        Write-Host "Git n'est pas installé ou n'est pas accessible." -ForegroundColor Red
        Write-Host "Installe Git pour Windows puis relance le script."
        Pause-Script
        exit 1
    }
}

function Test-RepositoryExists {
    return Test-Path (Join-Path $RepoDirectory ".git")
}

function Set-RepositoryLocation {
    if (-not (Test-RepositoryExists)) {
        Write-Host "Le dépôt n'est pas présent dans :" -ForegroundColor Yellow
        Write-Host $RepoDirectory
        Write-Host ""
        Write-Host "Commence par choisir l'option 1 pour le cloner." -ForegroundColor Yellow
        return $false
    }

    Set-Location $RepoDirectory
    return $true
}

function Configure-GitIdentity {
    if (-not (Set-RepositoryLocation)) {
        return
    }

    git config user.name $GitUserName
    git config user.email $GitUserEmail

    Write-Host ""
    Write-Host "Identité Git configurée pour ce dépôt :" -ForegroundColor Green
    Write-Host "Pseudo : $GitUserName"
    Write-Host "E-mail : $GitUserEmail"
}

function Clone-Repository {
    if (Test-RepositoryExists) {
        Write-Host "Le dépôt existe déjà dans :" -ForegroundColor Yellow
        Write-Host $RepoDirectory
        return
    }

    if (Test-Path $RepoDirectory) {
        Write-Host "Le dossier existe déjà, mais il ne semble pas être un dépôt Git :" -ForegroundColor Red
        Write-Host $RepoDirectory
        Write-Host ""
        Write-Host "Renomme ou supprime ce dossier avant de relancer le clonage."
        return
    }

    Write-Host "Clonage du dépôt..." -ForegroundColor Cyan

    git clone $RepoUrl $RepoDirectory

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Le clonage a échoué." -ForegroundColor Red
        return
    }

    Configure-GitIdentity

    Write-Host ""
    Write-Host "Dépôt cloné avec succès dans :" -ForegroundColor Green
    Write-Host $RepoDirectory
}

function Show-RepositoryStatus {
    if (-not (Set-RepositoryLocation)) {
        return
    }

    Write-Host "État actuel du dépôt :" -ForegroundColor Cyan
    Write-Host ""

    git status
}

function Pull-Repository {
    if (-not (Set-RepositoryLocation)) {
        return
    }

    Write-Host "Récupération des dernières modifications..." -ForegroundColor Cyan
    Write-Host ""

    git pull --rebase

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Le dépôt est à jour." -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "La récupération a rencontré un problème." -ForegroundColor Red
        Write-Host "Vérifie les éventuels conflits affichés ci-dessus."
    }
}

function Commit-And-Push {
    if (-not (Set-RepositoryLocation)) {
        return
    }

    Write-Host "État des modifications :" -ForegroundColor Cyan
    Write-Host ""

    git status --short

    $Changes = git status --porcelain

    if (-not $Changes) {
        Write-Host ""
        Write-Host "Aucune modification à envoyer." -ForegroundColor Yellow
        return
    }

    Write-Host ""
    $CommitMessage = Read-Host "Entre le message du commit"

    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        Write-Host "Le message de commit ne peut pas être vide." -ForegroundColor Red
        return
    }

    Write-Host ""
    Write-Host "Ajout des fichiers..." -ForegroundColor Cyan
    git add --all

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Impossible d'ajouter les fichiers." -ForegroundColor Red
        return
    }

    Write-Host "Création du commit..." -ForegroundColor Cyan
    git commit -m $CommitMessage

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Impossible de créer le commit." -ForegroundColor Red
        return
    }

    Write-Host ""
    Write-Host "Récupération des éventuelles modifications distantes..." -ForegroundColor Cyan
    git pull --rebase

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Le push est interrompu." -ForegroundColor Red
        Write-Host "Un conflit est peut-être présent. Résous-le avant de recommencer."
        return
    }

    Write-Host ""
    Write-Host "Envoi vers GitHub..." -ForegroundColor Cyan
    git push

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Modifications envoyées avec succès sur GitHub." -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "Le push a échoué." -ForegroundColor Red
        Write-Host "Vérifie ton authentification GitHub et les messages ci-dessus."
    }
}

function Open-RepositoryFolder {
    if (-not (Test-Path $RepoDirectory)) {
        Write-Host "Le dossier du dépôt n'existe pas encore." -ForegroundColor Yellow
        return
    }

    Start-Process explorer.exe $RepoDirectory
}

Test-GitInstalled

do {
    Write-Title

    Write-Host "Dépôt distant : $RepoUrl"
    Write-Host "Dossier local : $RepoDirectory"
    Write-Host ""

    Write-Host "1 - Cloner le dépôt"
    Write-Host "2 - Afficher l'état du dépôt"
    Write-Host "3 - Récupérer les dernières modifications"
    Write-Host "4 - Ajouter, commit et push"
    Write-Host "5 - Configurer le pseudo et l'adresse e-mail"
    Write-Host "6 - Ouvrir le dossier dans l'Explorateur"
    Write-Host "0 - Quitter"
    Write-Host ""

    $Choice = Read-Host "Choisis une option"

    switch ($Choice) {
        "1" {
            Write-Title
            Clone-Repository
            Pause-Script
        }

        "2" {
            Write-Title
            Show-RepositoryStatus
            Pause-Script
        }

        "3" {
            Write-Title
            Pull-Repository
            Pause-Script
        }

        "4" {
            Write-Title
            Commit-And-Push
            Pause-Script
        }

        "5" {
            Write-Title
            Configure-GitIdentity
            Pause-Script
        }

        "6" {
            Open-RepositoryFolder
        }

        "0" {
            Write-Host "Fermeture du script."
        }

        default {
            Write-Host "Option inconnue." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
while ($Choice -ne "0")