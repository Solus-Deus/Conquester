
        how_many = input('how many')
        if how_many == "":
            how_many = 100
        else:
            how_many = int(how_many)
        print(f"{how_many} new spalls coming!")
        for i in range(how_many):
            spall = Spalls()
            print(len(Spalls.query.filter_by().all()))
            if len(Spalls.query.filter_by().all()) != 0:
                new_connection = random.choice(Spalls.query.filter_by().all())
                print(f"connecting {spall} to {new_connection}!")
                spall.bridges.append(new_connection)
                new_connection.bridges.append(spall)
                print(f"{spall}'s connections now are {spall.bridges}")
                print(f"{new_connection}'s connections now are {new_connection.bridges}")
            db.session.add(spall)
        spalls = Spalls.query.filter_by().all()
        spallcount = len(spalls)
        for i in range(round(spallcount)):
            rs1 = random.choice(spalls)
            rs2 = random.choice(spalls)
            rs1.bridges.append(rs2)
            rs2.bridges.append(rs1)
        print(Spalls.query.filter_by().all())
        for i in Spalls.query.filter_by().all():
            print(f"{i}'s connections are {i.bridges}")
        input()
        db.session.commit()
        print("Commited! New info incoming:")
        print(Spalls.query.filter_by().all())
        for i in Spalls.query.filter_by().all():
            print(f"{i}'s connections are {i.bridges}")
        input()