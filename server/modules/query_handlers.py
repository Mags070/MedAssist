from logger import logger

def query_chain(chain,user_input:str):
    try:
        logger.debug(f"Running chain for input: {user_input}")
        result=chain({"query":user_input})
        response={
            "response":result["result"],
            "sources":[
                doc.metadata["source"]
                for doc in result["source_documents"]
                if doc.metadata.get("source")
            ]
        }
        logger.debug(f"Chain response:{response}")
        return response
    except Exception as e:
        logger.exception("Error on query chain")
        raise