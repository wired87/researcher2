from core.researcher2.researcher2.core import ResearchAgent

if __name__ =="__main__":
    r = ResearchAgent()
    r.run(
        prompt="Get top 10 gravity related publications relevant for thepretical physicists to extract as much useful equations to run a simulaiton from",
        use_dr_result_callable=r.research_workflow
    )