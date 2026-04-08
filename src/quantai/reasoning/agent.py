import os
from pathlib import Path
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool
from quantai.reasoning.symbolic_solver import SymbolicLogicEngine
from quantai.reasoning.market_data import PhysicalMarketGateway
from quantai.reasoning.visualization import DimensionalProjectionEngine

class AutonomousResearchEntity:
    def __init__(self, db_dir="faiss_db_vault"):
        self.db_dir = Path(os.getcwd()) / db_dir
        self.embedder = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-large-en-v1.5", 
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.llm = Ollama(model="llama3", temperature=0.0)
        self.symbolic_engine = SymbolicLogicEngine()
        self.market_gateway = PhysicalMarketGateway()
        self.visualizer = DimensionalProjectionEngine()
        self.vector_db = self._bind_memory_matrix()
        
        self.tools = self._forge_tool_array()
        self.agent_executor = self._forge_cognitive_loop()

    def _bind_memory_matrix(self):
        if not self.db_dir.exists(): return None
        return FAISS.load_local(str(self.db_dir), self.embedder, allow_dangerous_deserialization=True)

    def _query_literature(self, query: str) -> str:
        if not self.vector_db: return "Memory offline."
        return "\n".join([d.page_content for d in self.vector_db.similarity_search(query, k=3)])

    def _forge_tool_array(self) -> list:
        return [
            Tool(name="Retrieve_Literature", func=self._query_literature, description="Fetches exact mathematical theorems from memory."),
            Tool(name="Execute_Symbolic_Math", func=self.symbolic_engine.evaluate_expression, description="Executes deterministic C-level arithmetic. Input: pure SymPy string."),
            Tool(name="Fetch_Empirical_Variance", func=self.market_gateway.fetch_empirical_variance, description="Acquires physical market variance for a ticker."),
            Tool(name="Render_Visualization", func=lambda args: self.visualizer.export_stochastic_path(*eval(args)), description="Plots data arrays.")
        ]

    def _forge_cognitive_loop(self):
        # Apex Deterministic ReAct Prompt
        template = """You are an apex quantitative research intelligence.
        Your singular function is the discovery, formalization, and rigorous proof of novel mathematical structures.
        You have access to the following deterministic tools:

        {tools}

        Strict Execution Protocol:
        Question: the mathematical input you must resolve
        Thought: deduce the precise quantitative logic required
        Action: select strictly one of [{tool_names}]
        Action Input: the absolute input string for the action
        Observation: the physical output of the tool
        ... (this Thought/Action/Action Input/Observation matrix can repeat until derived)
        Thought: The derivation is mathematically complete.
        Final Answer: the unassailable theoretical synthesis

        Commence!

        Question: {input}
        Thought:{agent_scratchpad}"""
        
        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def execute_research_directive(self, directive: str):
        print(f"\n[+] AGENT ACTIVATED. EXECUTING DIRECTIVE: {directive}")
        try:
            response = self.agent_executor.invoke({"input": directive})
            print(f"\n[+] FINAL SYNTHESIS:\n{response['output']}")
        except Exception as e:
            print(f"\n[-] COGNITIVE FRACTURE: {str(e)}")