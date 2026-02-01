<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> Laissez les modèles de langage (LLM) vous aider à réaliser vos analyses de régression avec Stata. ✨</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](../../../../README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](../cn/README.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](README.md)
[![sp](https://img.shields.io/badge/Idioma-Español-green.svg)](../sp/README.md)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](../../../../LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/stata-mcp/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/stata-mcp)

---
**Notes**: While we strive to make open source accessible to everyone, we regret that we can no longer maintain the Apache-2.0 License. Due to individuals directly copying this project and claiming to be its maintainers, we have decided to change the license to AGPL-3.0 to prevent misuse of the project in ways that go against our original vision.

**Notes**: 尽管我们希望尽可能让所有人都能从开源中获益，但我们很遗憾地宣布无法继续保持 Apache-2.0 License。由于有人直接抄袭本项目并标榜其为项目维护者，我们不得不将 License 更改为 AGPL-3.0，以防止有人滥用本项目进行违背项目初心的事情。

<details>
<summary>Reason</summary>

**Background**: @jackdark425's [repository](https://github.com/jackdark425/aigroup-stata-mcp) directly copied this project and claimed to be the sole maintainer. We welcome open source collaboration based on forks, including but not limited to adding new features, fixing existing bugs, or providing valuable suggestions for the project, but we firmly oppose plagiarism and false attribution.

**Update**: The infringing project has been taken down via GitHub DMCA. Click [here](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md) to learn about.

**背景**: @jackdark425 的[仓库](https://github.com/jackdark425/aigroup-stata-mcp)直接抄袭了本项目并标榜为项目唯一维护者。我们欢迎基于fork的开源协作，包括但不限于添加新的feature、修改已有bug或对项目提出您宝贵的意见，但坚决反对抄袭和虚假署名行为。

**更新**: 侵权项目已通过GitHub DMCA被takedown，点击[这里](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md)查看详情。

</details>

---
**Note :** Après la sortie de la v2.0.0, ce document ne sera plus mis à jour. Pour plus de contenu, veuillez consulter le README en anglais [ici](../../../../README.md).

Nouveauté : Vous pouvez maintenant utiliser Stata-MCP en mode agent, plus d'informations [ici](../../../agent_examples/README.md).


> Vous cherchez d'autres?
>
> - [Trace DID](https://github.com/asjadnaqvi/DiD) : Si vous voulez récupérer les informations les plus récentes sur DID (Difference-in-Difference), cliquez [ici](https://asjadnaqvi.github.io/DiD/). Il y a maintenant une traduction française par [Sepine Tam](https://github.com/sepine) et [StataMCP-Team](https://github.com/statamcp-team) 🎉
> - Utilisation de Jupyter Lab (Important: Stata 17+) [ici](../../JupyterStata.md)
> - [NBER-MCP](https://github.com/sepinetam/NBER-MCP) & [AER-MCP](https://github.com/sepinetam/AER-MCP) 🔧 en cours de construction
> - [Econometrics-Agent](https://github.com/FromCSUZhou/Econometrics-Agent)
> - [TexIV](https://github.com/sepinetam/TexIV) : Un cadre basé sur l'apprentissage automatique qui transforme les données textuelles en variables utilisables pour la recherche empirique en utilisant des techniques avancées de NLP et de ML
> - Une intégration VScode ou Cursor [ici](https://github.com/hanlulong/stata-mcp). Vous êtes perdu? 💡 [Différence](../../Difference.md)

## 💡 Démarrage Rapide
### Mode Agent
Les détails du mode agent se trouvent [ici](../../../agent_examples/README.md).

```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv sync
uv pip install -e .

stata-mcp --version  # pour tester si stata-mcp est installé avec succès.
stata-mcp --agent  # maintenant vous pouvez profiter du mode agent stata-mcp.
```

ou vous pouvez l'utiliser directement avec `uvx` :
```bash
uvx stata-mcp --version  # pour tester s'il peut être utilisé sur votre ordinateur.
uvx stata-mcp --agent
```

### Mode Client Chat-Bot IA
> La configuration standard nécessite que Stata soit installé sur le chemin par défaut et que l'interface en ligne de commande de Stata (pour macOS et Linux) soit disponible.

Le fichier json de configuration standard est le suivant, vous pouvez personnaliser votre configuration en ajoutant des variables d'environnement.
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

Pour des informations d'utilisation plus détaillées, consultez le [guide d'utilisation](../../Usages/Usage.md).

Et pour une utilisation avancée, visitez le [Guide avancé](../../Usages/Advanced.md)

### Prérequis
- [uv](https://github.com/astral-sh/uv) - Gestionnaire de paquets et d'environnements virtuels
- Claude, Cline, ChatWise, ou autre service LLM
- Licence Stata
- Votre clé API pour le service LLM

> Notes:
> 1. Si vous êtes situé en Chine, un court document d'utilisation d'uv est disponible [ici](../../ChinaUsers/uv.md).
> 2. Claude est le meilleur choix pour Stata-MCP, pour les utilisateurs chinois, je recommande d'utiliser DeepSeek comme fournisseur de modèle car il est peu coûteux et puissant, et son score est le plus élevé parmi les fournisseurs chinois, si vous êtes intéressé, visitez le rapport [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

### Installation
Pour la nouvelle version, il n'est plus nécessaire d'installer le paquet `stata-mcp`. Utilisez simplement les commandes suivantes pour vérifier que votre ordinateur peut l'exécuter :
```bash
uvx stata-mcp --usable
uvx stata-mcp --version
```

Si vous souhaitez l'utiliser localement, vous pouvez l'installer via pip ou télécharger le code source puis le compiler.

**Installation via pip**
```bash
pip install stata-mcp
```

**Télécharger le code source et compiler**
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv build
```
Vous trouverez ensuite le binaire `stata-mcp` compilé dans le répertoire `dist`. Vous pouvez l'utiliser directement ou l'ajouter à votre PATH.

Par exemple:
```bash
uvx /path/to/your/whl/stata_mcp-1.13.0-py3-non-any.whl  # modifiez le nom du fichier selon votre version
```

## 📝 Documentation
- Pour des informations d'utilisation plus détaillées, consultez le [guide d'utilisation](../../Usages/Usage.md).
- Utilisation avancée, visitez le [Guide avancé](../../Usages/Advanced.md)
- Quelques questions, visitez les [Questions](../../Usages/Questions.md)
- Différence avec [Stata-MCP@hanlulong](https://github.com/hanlulong/stata-mcp), visitez la [Différence](../../Difference.md)

## 💡 Questions
- [Cherry Studio 32000 wrong](../../Usages/Questions.md#cherry-studio-32000-wrong)
- [Cherry Studio 32000 error](../../Usages/Questions.md#cherry-studio-32000-error)
- [Support Windows](../../Usages/Questions.md#windows-supports)
- [Problèmes de réseau](../../Usages/Questions.md#network-errors-when-running-stata-mcp)

## 🚀 Feuille de Route
- [x] Support macOS
- [x] Support Windows
- [ ] Intégrations supplémentaires de LLM
- [ ] Optimisations de performance

## ⚠️ Avertissement
Ce projet est destiné uniquement à des fins de recherche. Je ne suis pas responsable des dommages causés par ce projet. Veuillez vous assurer que vous disposez des licences appropriées pour utiliser Stata.

Pour plus d'informations, consultez la [Déclaration](../../Rights/Statement.md).

## 🐛 Signaler des Problèmes
Si vous rencontrez des bugs ou avez des demandes de fonctionnalités, veuillez [ouvrir un ticket](https://github.com/sepinetam/stata-mcp/issues/new).

## 📄 Licence
[GNU Affero General Public License v3.0](../../../../LICENSE)

## 📚 Citation
Si vous utilisez Stata-MCP dans vos recherches, veuillez citer ce référentiel en utilisant l'un des formats suivants:

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {Stata-MCP: Let LLM help you achieve your regression analysis with Stata},
  year = {2025},
  url = {https://github.com/sepinetam/stata-mcp},
  version = {1.13.0}
}
```

### APA
```
Song Tan. (2025). Stata-MCP: Let LLM help you achieve your regression analysis with Stata (Version 1.13.0) [Computer software]. https://github.com/sepinetam/stata-mcp
```

### Chicago
```
Song Tan. 2025. "Stata-MCP: Let LLM help you achieve your regression analysis with Stata." Version 1.13.0. https://github.com/sepinetam/stata-mcp.
```

## 📬 Contact
Email : [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

Ou contribuez directement en soumettant une [Pull Request](https://github.com/sepinetam/stata-mcp/pulls) ! Nous accueillons les contributions de toutes sortes, des corrections de bugs aux nouvelles fonctionnalités.

## ❤️ Remerciements
L'auteur remercie sincèrement l'équipe officielle de Stata pour son soutien et la licence Stata pour avoir autorisé le développement du test.

## ✨ Histoire des étoiles

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)