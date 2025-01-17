--------------------------------- MODULE raft_le ---------------------------------
EXTENDS Naturals, FiniteSets, Sequences, TLC

\* The set of server IDs
CONSTANTS Server

\* Server states.
CONSTANTS Follower, Candidate, Leader

\* A reserved value.
CONSTANTS Nil

\* Message types:
CONSTANTS RequestVoteRequest, RequestVoteResponse

CONSTANTS TimeoutLimit, RestartLimit

----
\* Global variables

\* A bag of records representing requests and responses sent from one server
\* to another. TLAPS doesn't support the Bags module, so this is a function
\* mapping Message to Nat.
VARIABLE messages

\* Constraints variable by Dong Wang
VARIABLE timeoutNum, restartNum
----
\* The following variables are all per server (functions with domain Server).

\* The server's term number.
VARIABLE currentTerm
\* The server's state (Follower, Candidate, or Leader).
VARIABLE state
\* The candidate the server voted for in its current term, or
\* Nil if it hasn't voted for any.
VARIABLE votedFor
serverVars == <<currentTerm, state, votedFor>>

\* The set of servers from which the candidate has received a vote in its
\* currentTerm.
VARIABLE votesGranted

VARIABLE lastSnapshot


\* End of per server variables.
----

\* All variables; used for stuttering (asserting state hasn't changed).
vars == <<messages, serverVars, votesGranted, timeoutNum, restartNum>>

----
\* Helpers

\* The set of all quorums. This just calculates simple majorities, but the only
\* important property is that every quorum overlaps with every other.
Quorum == {i \in SUBSET(Server) : Cardinality(i) * 2 > Cardinality(Server)}          


Send(m) == /\ m \notin messages 
           /\ messages' = messages \union {m}
Reply(response, request) == messages' = (messages \ {request}) \union {response} 
Discard(m) == /\ m \in messages 
              /\ messages' = messages \ {m}


\* Return the maximum value from a set, or undefined if the set is empty.
Max(s) == CHOOSE x \in s : \A y \in s : x >= y
----
\* Define initial values for all variables

InitServerVars == /\ currentTerm = [i \in Server |-> 0]
                  /\ state       = [i \in Server |-> Follower]
                  /\ votedFor    = [i \in Server |-> Nil]
                  /\ votesGranted   = [i \in Server |-> {}]
                  /\ lastSnapshot = [i \in Server |-> 0]
\* The values nextIndex[i][i] and matchIndex[i][i] are never read, since the
\* leader does not send itself messages. It's still easier to include these
\* in the functions.
InitConstraints == /\ restartNum = 0
                   /\ timeoutNum = 0
Init == /\ messages = {}
        /\ InitServerVars
        /\ InitConstraints
----
\* Define state transitions in leader election

\* Candidate i sends j a RequestVote request.
RequestVote(i, j) ==
    /\ state[i] = Candidate
    /\ i \notin votesGranted[j]
    /\ Send([mtype         |-> RequestVoteRequest,
             mterm         |-> currentTerm[i],
             msource       |-> i,
             mdest         |-> j])
    /\ UNCHANGED <<serverVars, votesGranted, restartNum, timeoutNum, lastSnapshot>>
                   
\* Server i times out and starts a new election.
Timeout(i) == /\ state[i] \in {Follower}
              /\ state' = [state EXCEPT ![i] = Candidate]
              /\ currentTerm' = [currentTerm EXCEPT 
                                ![i] = currentTerm[i] + 1]
              \* Most implementations would probably just set the local vote
              \* atomically, but messaging localhost for it is weaker.
              /\ votedFor' = [votedFor EXCEPT ![i] = Nil]
              /\ votesGranted'   = [votesGranted EXCEPT 
                                   ![i] = {}]
              /\ timeoutNum'     = timeoutNum + 1
              /\ timeoutNum      < TimeoutLimit
              /\ UNCHANGED <<messages, restartNum>>

UpdateTerm(i, j, m) ==
    /\ m.mterm > currentTerm[i]
    /\ currentTerm'    = [currentTerm EXCEPT ![i] = m.mterm]
    /\ state'          = [state       EXCEPT ![i] = Follower]
    /\ votedFor'       = [votedFor    EXCEPT ![i] = Nil]
       \* messages is unchanged so m can be processed further.
    /\ UNCHANGED <<messages, lastSnapshot>>

\* Server i receives a RequestVote request from server j with
\* m.mterm <= currentTerm[i].
HandleRequestVoteRequest(i, j, m) ==
    LET grant == \/ /\ votedFor[i] \in {Nil, j}
                    /\ m.mterm >= currentTerm[i]
                 \/ /\ i = j
        newTerm == Max({m.mterm,currentTerm[i]})
    IN
       /\ \/ /\ m.mterm > currentTerm[i]
             /\ currentTerm' = [currentTerm EXCEPT ![i] = m.mterm]
             /\ state'       = [state       EXCEPT ![i] = Follower]
          \/ /\ m.mterm <= currentTerm[i]
             /\ UNCHANGED <<currentTerm,state>>
             
       /\ \/ /\ grant  
             /\ votedFor' = [votedFor EXCEPT ![i] = j]
          \/ /\ ~grant 
             /\ UNCHANGED votedFor
       /\ Reply([mtype        |-> RequestVoteResponse,
                 mterm        |-> newTerm,
                 mvoteGranted |-> grant,
                 msource      |-> i,
                 mdest        |-> j],
                 m)    
       /\ UNCHANGED <<restartNum, timeoutNum, votesGranted, lastSnapshot>>

\* Server i receives a RequestVote response from server j with
\* m.mterm = currentTerm[i].
HandleRequestVoteResponse(i, j, m) ==
    \* This tallies votes even when the current state is not Candidate, but
    \* they won't be looked at, so it doesn't matter. 
    \* /\ Assert(m.mterm = currentTerm[i], <<m.mterm, currentTerm[i]>>)
    /\ \/ /\ m.mterm > currentTerm[i]
          /\ state'        = [state EXCEPT ![i] = Follower]
          /\ currentTerm'  = [currentTerm EXCEPT ![i] = m.mterm]
          /\ votedFor'     = [votedFor EXCEPT ![i] = Nil]
          /\ votesGranted' = [votesGranted EXCEPT ![i] = {}]
          /\ UNCHANGED <<restartNum, timeoutNum>>
       \/ /\ m.mterm = currentTerm[i]
          /\ \/ /\ m.mvoteGranted
                /\ votesGranted' = [votesGranted EXCEPT ![i] =
                                    votesGranted[i] \cup {j}]
             \/ /\ ~m.mvoteGranted
                /\ UNCHANGED <<votesGranted>>
          /\ UNCHANGED <<serverVars,restartNum, timeoutNum, lastSnapshot>>
    /\ Discard(m)

\* Receive a message.
Receive(m) ==
    LET i == m.mdest
        j == m.msource
    IN \* Any RPC with a newer term causes the recipient to advance
       \* its term first. Responses with stale terms are ignored.
       \/ UpdateTerm(i, j, m)
       \/ /\ m.mtype = RequestVoteRequest
          /\ HandleRequestVoteRequest(i, j, m)
       \/ /\ m.mtype = RequestVoteResponse
          /\ \/ DropStaleResponse(i, j, m)
             \/ HandleRequestVoteResponse(i, j, m)
       \/ /\ m.mtype = AppendEntriesRequest
          /\ HandleAppendEntriesRequest(i, j, m)
       \/ /\ m.mtype = AppendEntriesResponse
          /\ \/ DropStaleResponse(i, j, m)
             \/ HandleAppendEntriesResponse(i, j, m)

TakeSnapshot(i) == 
   /\ lastSnapshot' = [lastSnapshot EXCEPT ![i] = commitIndex[i]]
   /\ UNCHANGED <<messages, serverVars, candidateVars, leaderVars, logVars, envVars>>

\* Candidate i transitions to leader.
BecomeLeader(i) ==
    /\ state[i] = Candidate
    /\ votesGranted[i] \in Quorum
    /\ state'      = [state EXCEPT ![i] = Leader]
    /\ UNCHANGED <<messages, currentTerm, votedFor, votesGranted, restartNum, timeoutNum, lastSnapshot>>

Restart(i) == 
    /\ \/ state[i] = Candidate
       \/ state[i] = Leader 
    /\ state'        = [state EXCEPT ![i] = Follower]
    /\ votesGranted' = [votesGranted EXCEPT ![i] = {}]
    /\ restartNum'   = restartNum + 1
    /\ restartNum    < RestartLimit
    /\ UNCHANGED <<messages, currentTerm, votedFor, timeoutNum, lastSnapshot>>
----
\* Defines how the variables may transition.
Next ==\/ \E i \in Server : Timeout(i)
       \/ \E i,j \in Server : RequestVote(i, j)  
       \/ \E i \in Server : BecomeLeader(i)
       \/ \E m \in messages : Receive(m)
       \/ \E i \in Server : Restart(i)
       \/ \E i,j \in Server : TakeSnapshot(i)

\* The specification must start with the initial state and transition according
\* to Next.
Spec == Init /\ [][Next]_vars
===============================================================================